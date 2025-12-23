from pydantic import BaseModel
from datetime import datetime

class ClientSchema(BaseModel):
    name: str
    email: str
    phone: str

    class Config:
        from_attributes = True  

class ClientResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    total_billed: int
    created_at: datetime

    class Config:
        from_attributes = True  