from pydantic import BaseModel
from datetime import datetime

class UserSchema(BaseModel):
    username: str
    email: str
    password: str
    role: str | None = None
    company_name: str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    company_name: str | None = None

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class UserResponseSchema(BaseModel):
    username: str
    email: str
    role: str | None = None
    company_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserToken(BaseModel):
    token: str
    message: str

    class Config:
        from_attributes = True
