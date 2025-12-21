from pydantic import BaseModel
from datetime import date

class QuoteSchema(BaseModel):
    client_id: int
    status: str
    subtotal: float
    tax: float
    total: float
    expiry_date: date

    class Config:
        from_attributes = True  

class QuoteResponseSchema(BaseModel):
    id: int
    client_id: int
    status: str
    subtotal: float
    tax: float
    total: float
    expiry_date: date

    class Config:
        from_attributes = True  