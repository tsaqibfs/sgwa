from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class RequestCreate(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    title: str=Field(min_length=5,max_length=150)
    description: str=Field(min_length=20,max_length=5000)


class StatusChange(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    version: int=Field(ge=1)
    status: Literal['pending','processing','escalated','approved','rejected']
    note: str=Field(default='',max_length=2000)


class Reroute(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    version: int=Field(ge=1)
    agency_id: int=Field(gt=0)
    note: str=Field(min_length=1,max_length=2000)
