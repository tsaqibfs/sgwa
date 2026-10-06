from pydantic import BaseModel,ConfigDict,Field
from typing import Literal


class RouteUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    agency_ids:list[int]=Field(min_length=1,max_length=20)


class TaskDecision(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    request_version:int=Field(ge=1)
    task_version:int=Field(ge=1)
    status:Literal['processing','approved','rejected','escalated']
    note:str=Field(default='',max_length=2000)


class ReviewRoute(RouteUpdate):
    version:int=Field(ge=1)
    note:str=Field(min_length=1,max_length=2000)
