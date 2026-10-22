from datetime import date,datetime,time,timedelta
from typing import Literal
import re
from pydantic import BaseModel,ConfigDict,Field,model_validator,field_validator

Status=Literal['pending','processing','escalated','approved','rejected']
STATUSES=('pending','processing','escalated','approved','rejected')

class ReportFilters(BaseModel):
    model_config=ConfigDict(extra='forbid')
    date_from:date|None=None
    date_to:date|None=None
    status:Status|None=None
    agency_id:int|None=Field(default=None,gt=0)

    @field_validator('date_from','date_to',mode='before')
    @classmethod
    def iso_date(cls,value):
        if value is None or (isinstance(value,date) and not isinstance(value,datetime)):return value
        if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',value):
            raise ValueError('Tanggal harus memakai format YYYY-MM-DD.')
        return value

    @model_validator(mode='after')
    def valid_dates(self):
        if self.date_from and self.date_to and self.date_from>self.date_to:
            raise ValueError('Tanggal akhir tidak boleh sebelum tanggal awal.')
        try:
            if self.date_from:datetime.combine(self.date_from,time.min)-timedelta(hours=7)
            if self.date_to:datetime.combine(self.date_to,time.max)-timedelta(hours=7)+timedelta(microseconds=1)
        except OverflowError as exc:raise ValueError('Tanggal berada di luar rentang waktu yang didukung.') from exc
        return self

class ReportQuery(ReportFilters):
    page:int=Field(default=1,ge=1)
    page_size:int=Field(default=20,ge=1,le=100)

class AgencyRef(BaseModel):
    id:int
    name:str

class ReportClassification(BaseModel):
    predicted_agency_code:str
    confidence:float
    model_version:str

class ReportRow(BaseModel):
    id:int
    reference:str
    title:str
    status:Status
    created_at:str
    updated_at:str
    primary_agency:AgencyRef|None
    agencies:list[AgencyRef]
    classification:ReportClassification|None

class ReportSummary(BaseModel):
    total:int
    by_status:dict[str,int]
    completed_count:int
    completion_rate:float|None
    overdue_count:int
    average_completed_hours:float|None

class ReportResponse(BaseModel):
    filters:ReportFilters
    generated_at:str
    page:int
    page_size:int
    total:int
    summary:ReportSummary
    items:list[ReportRow]
