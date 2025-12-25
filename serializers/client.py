from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class ClientBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class ClientResponse(ClientBase):
    id: int
    user_id: int
    total_billed: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True