from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, field_validator
import re
# from typing import List, Optional

class ResponseContactModel(BaseModel):
    id: int = Field(default=1, ge=1)
    name: str
    lastname: str
    email: str
    phone: str
    birthday: date
    note: str


class ContactModel(BaseModel):
    name: str
    lastname: str
    email: EmailStr
    phone: str
    birthday: date
    note: str

    @field_validator("phone")
    @classmethod
    def adopt_phone(cls, v: str):
        pattern_phone =  r"^(?:\+\d{1,3})?\s*(?:\(\d{2,5}\)|\d{2,5})?" \
                         r"\s*\d{1,3}(?:\s*-)?\s*\d{1,3}(?:\s*-)?\s*\d{1,3}\s*$"
        v = " ".join(v.split())
        v = v.replace(" - ", "-").replace(" -", "-").replace("- ", "-")
        if not re.search(pattern_phone, v):
            raise ValueError(f"Wrong phone number '{v}'")
        return v


class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)


class UserDb(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str

    class Config:
        # orm_mode = True
        from_attributes = True

class ResponseUserModel(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr
