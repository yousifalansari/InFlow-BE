from pydantic import BaseModel, Field, condecimal
from datetime import date

class QuoteBase(BaseModel):
    client_id: int
    status: str = "draft"
    subtotal: condecimal(max_digits=10, decimal_places=2)
    tax: condecimal(max_digits=10, decimal_places=2) = Field(default=0)
    total: condecimal(max_digits=10, decimal_places=2)
    expiry_date: date | None = None

class QuoteCreate(QuoteBase):
    pass

class QuoteUpdate(BaseModel):
    client_id: int | None = None
    status: str | None = None
    subtotal: condecimal(max_digits=10, decimal_places=2) | None = None
    tax: condecimal(max_digits=10, decimal_places=2) | None = None
    total: condecimal(max_digits=10, decimal_places=2) | None = None
    expiry_date: date | None = None

class QuoteResponse(QuoteBase):
    id: int
    
    class Config:
        from_attributes = True