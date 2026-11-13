from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from backend.app.models import User
from backend.app.reports.forecast import forecast_agency, forecast_volume, history_end


def test_staff_cannot_select_another_department_and_citizens_are_denied():
    staff = User(role='staff', agency_id=4)
    assert forecast_agency(staff, None) == 4
    for actor, agency_id in [(staff, 5), (User(role='citizen'), 4), (User(role='staff'), None)]:
        with pytest.raises(HTTPException, match='403'):
            forecast_agency(actor, agency_id)


def test_history_excludes_current_wib_day():
    assert history_end(datetime(2026, 11, 12, 18, tzinfo=timezone.utc)) == date(2026, 11, 12)


def test_short_history_stays_unavailable_and_missing_days_count_as_zero():
    end = date(2026, 11, 12)
    assert forecast_volume({end: 9}, end)['status'] == 'insufficient_data'
    result = forecast_volume({end - timedelta(days=59): 1}, end)
    assert result['history_days'] == 60
    assert result['history'][-1] == {'date': end, 'count': 0}
    assert all(point['estimate'] == 0 for point in result['forecast'])


def test_weekly_pattern_backtest_and_forecast():
    end = date(2026, 11, 12)
    counts = {end - timedelta(days=i): i % 7 + 1 for i in range(80)}
    result = forecast_volume(counts, end)
    assert result['method'] == 'same_weekday'
    assert result['evaluation']['baseline_mae'] == 0
    assert result['evaluation']['moving_average_mae'] > 0
    assert [row['estimate'] for row in result['forecast']] == [7, 6, 5, 4, 3, 2, 1]
