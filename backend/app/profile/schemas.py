from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    agency_id: int | None
    phone: str | None
    address: str | None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)

    @model_validator(mode='after')
    def valid_name(self):
        if 'name' in self.model_fields_set and self.name is None:
            raise ValueError('Nama wajib diisi.')
        return self


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra='forbid')
    current_password: str = Field(min_length=10, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)
