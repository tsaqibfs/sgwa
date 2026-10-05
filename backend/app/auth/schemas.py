from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Credentials(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    email: EmailStr
    password: str=Field(min_length=10,max_length=128)

    @field_validator('email')
    @classmethod
    def normalize_email(cls,value):
        return str(value).lower()


class Register(Credentials):
    name: str=Field(min_length=2,max_length=150)


class UserOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    agency_id: int|None
    active: bool
