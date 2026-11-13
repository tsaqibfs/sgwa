from datetime import date, datetime, time, timedelta, timezone
from statistics import mean
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from backend.app.models import Agency, Request, RequestWorkflow, User
from backend.app.reports.schemas import AgencyRef

WIB_OFFSET = timedelta(hours=7)
HISTORY_LIMIT = 120
MIN_HISTORY = 60
HORIZON = 7
METHODS = ('same_weekday', 'moving_average')


class Observation(BaseModel):
    date: date
    count: int


class Estimate(BaseModel):
    date: date
    estimate: int


class Backtest(BaseModel):
    days: int
    baseline_mae: float
    moving_average_mae: float


class ForecastResponse(BaseModel):
    agency: AgencyRef
    status: Literal['ready', 'insufficient_data']
    history_days: int
    minimum_history_days: int
    history: list[Observation]
    forecast: list[Estimate]
    method: Literal['same_weekday', 'moving_average'] | None = None
    evaluation: Backtest | None = None


def forecast_agency(actor: User, agency_id: int | None) -> int:
    if actor.role == 'admin':
        if agency_id is None:
            raise HTTPException(422, 'Pilih dinas untuk melihat prakiraan.')
        return agency_id
    if actor.role == 'staff' and actor.agency_id and agency_id in (None, actor.agency_id):
        return actor.agency_id
    raise HTTPException(403, 'Anda tidak memiliki akses ke prakiraan dinas ini.')


def history_end(now: datetime) -> date:
    utc = now.astimezone(timezone.utc).replace(tzinfo=None) if now.tzinfo else now
    return (utc + WIB_OFFSET).date() - timedelta(days=1)


def forecast_volume(counts: dict[date, int], end: date) -> dict:
    start = end - timedelta(days=HISTORY_LIMIT - 1)
    first = min((day for day, count in counts.items() if start <= day <= end and count), default=end + timedelta(days=1))
    days = (end - first).days + 1
    dates = [first + timedelta(days=offset) for offset in range(days)]
    volumes = [counts.get(day, 0) for day in dates]
    result = {
        'status': 'insufficient_data',
        'history_days': days,
        'minimum_history_days': MIN_HISTORY,
        'history': [{'date': day, 'count': volume} for day, volume in zip(dates, volumes)],
        'forecast': [],
    }
    if days < MIN_HISTORY:
        return result

    def estimate(week: list[int], method: str) -> list[int]:
        if method == 'same_weekday':
            return week
        return [round(mean(week))] * HORIZON

    # Each test week uses only the immediately preceding, fully observed week.
    errors = {}
    for method in METHODS:
        errors[method] = mean(
            abs(actual - predicted)
            for offset in (days - 2 * HORIZON, days - HORIZON)
            for actual, predicted in zip(
                volumes[offset:offset + HORIZON],
                estimate(volumes[offset - HORIZON:offset], method),
            )
        )
    method = min(METHODS, key=errors.__getitem__)
    result.update(
        status='ready',
        method=method,
        evaluation={
            'days': 2 * HORIZON,
            'baseline_mae': round(errors['same_weekday'], 2),
            'moving_average_mae': round(errors['moving_average'], 2),
        },
        forecast=[
            {'date': end + timedelta(days=offset), 'estimate': volume}
            for offset, volume in enumerate(estimate(volumes[-HORIZON:], method), start=1)
        ],
    )
    return result


def read_forecast(db: Session, actor: User, agency_id: int | None, now: datetime) -> ForecastResponse:
    target = forecast_agency(actor, agency_id)
    agency = db.get(Agency, target)
    if agency is None:
        raise HTTPException(404, 'Dinas tidak ditemukan.')

    end = history_end(now)
    start_utc = datetime.combine(end - timedelta(days=HISTORY_LIMIT - 1), time.min) - WIB_OFFSET
    end_utc = datetime.combine(end + timedelta(days=1), time.min) - WIB_OFFSET
    local_day = func.date(func.timestampadd(text('HOUR'), 7, Request.created_at))
    statement = (
        select(local_day, func.count())
        .select_from(RequestWorkflow)
        .join(Request, Request.id == RequestWorkflow.request_id)
        .where(RequestWorkflow.agency_id == target, Request.created_at >= start_utc, Request.created_at < end_utc)
        .group_by(local_day)
    )
    result = forecast_volume(dict(db.execute(statement).all()), end)
    return ForecastResponse(agency=AgencyRef(id=agency.id, name=agency.name), **result)
