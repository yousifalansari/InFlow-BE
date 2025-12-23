from pydantic import BaseModel
from datetime import datetime

class UserSchema(BaseModel):
    username: str
    email: str
    password: str
    company_name: str | None = None

    class Config:
        orm_mode = True

class UserResponseSchema(BaseModel):
    username: str
    email: str
    role: str | None = None
    company_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserToken(BaseModel):
    token: str
    message: str

    class Config:
        orm_mode = True
