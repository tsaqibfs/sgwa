from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal


class RequestCreate(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    title: str=Field(min_length=5,max_length=150)
    description: str=Field(min_length=20,max_length=5000)
    form_version_id: int|None=Field(default=None,gt=0)
    form_answers: dict|None=None
    attachment_ids: list[int]=Field(default_factory=list)

    @model_validator(mode='after')
    def paired_form(self):
        if (self.form_version_id is None)!=(self.form_answers is None):
            raise ValueError('Versi formulir dan jawaban harus dikirim bersama.')
        return self


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
