from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator


@dataclass(frozen=True)
class Prediction:
    agency_code: str
    probabilities: dict[str, float]
    confidence: float
    known_features: bool
    model_version: str
    threshold: float = .70
    auto_routing_enabled: bool = True


class FeedbackCreate(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_revision: int=Field(ge=0)
    training_text: str=Field(min_length=10,max_length=5000)
    corrected_code: str=Field(min_length=2,max_length=50)
    provenance: Literal['synthetic_demo','real']
    family_key: str|None=Field(default=None,min_length=1,max_length=80,pattern=r'^[a-z0-9_-]+$')
    reason: str=Field(min_length=3,max_length=1000)
    idempotency_key: str=Field(min_length=1,max_length=100)

    @field_validator('corrected_code')
    @classmethod
    def catalog_label(cls,value):
        from backend.app.agencies.catalog import AGENCIES
        if value not in {code for code,_ in AGENCIES}:raise ValueError('Pilih salah satu dari 25 kelas katalog')
        return value


class FeedbackReview(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_revision: int=Field(ge=1)
    decision: Literal['verified','rejected']
    note: str=Field(min_length=3,max_length=1000)


class ModelActivation(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_revision: int=Field(ge=0)
    reason: str=Field(min_length=3,max_length=1000)
