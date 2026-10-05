from pydantic import BaseModel,ConfigDict,Field
from backend.app.auth.schemas import Register


class AgencyCreate(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    code: str=Field(min_length=2,max_length=50,pattern=r'^[a-z][a-z0-9_-]+$')
    name: str=Field(min_length=2,max_length=150)
    description: str=Field(default='',max_length=2000)


class AgencyUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    name: str|None=Field(default=None,min_length=2,max_length=150)
    description: str|None=Field(default=None,max_length=2000)
    active: bool|None=None


class StaffCreate(Register):
    agency_id: int=Field(gt=0)


class StaffUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    name: str|None=Field(default=None,min_length=2,max_length=150)
    agency_id: int|None=Field(default=None,gt=0)
    active: bool|None=None
