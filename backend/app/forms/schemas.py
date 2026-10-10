from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FieldDefinition(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)
    key: str = Field(pattern=r'^[a-z][a-z0-9_]*$', max_length=50)
    label: str = Field(min_length=1, max_length=150)
    type: Literal['text','textarea','number','date','select','checkbox']
    required: bool = False
    min_length: int | None = Field(default=None, ge=0, le=5000)
    max_length: int | None = Field(default=None, ge=1, le=5000)
    min_value: float | None = None
    max_value: float | None = None
    options: list[str] = Field(default_factory=list, max_length=50)

    @model_validator(mode='after')
    def constraints(self):
        if self.type not in ('text','textarea') and (self.min_length is not None or self.max_length is not None):
            raise ValueError('Batas panjang hanya untuk teks.')
        if self.type != 'number' and (self.min_value is not None or self.max_value is not None):
            raise ValueError('Batas angka hanya untuk field angka.')
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError('Batas panjang tidak valid.')
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            raise ValueError('Batas angka tidak valid.')
        if self.type == 'select':
            if not self.options or len(set(self.options)) != len(self.options) or any(not x.strip() or len(x)>150 for x in self.options):
                raise ValueError('Pilihan wajib unik dan tidak kosong.')
        elif self.options:
            raise ValueError('Pilihan hanya untuk dropdown.')
        return self


class FormSchema(BaseModel):
    model_config = ConfigDict(extra='forbid')
    fields: list[FieldDefinition] = Field(min_length=1, max_length=30)

    @model_validator(mode='after')
    def unique_keys(self):
        if len({field.key for field in self.fields}) != len(self.fields):
            raise ValueError('Key field harus unik.')
        return self


class FormCreate(FormSchema):
    agency_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=150)


class DraftUpdate(FormSchema):
    expected_version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=2, max_length=150)


class Publish(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=1)


class FormActive(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    active: bool
