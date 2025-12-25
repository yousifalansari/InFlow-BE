from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

class LineItemBase(BaseModel):
    description: str
    quantity: int
    rate: float

class LineItemCreate(LineItemBase):
    pass

class LineItemResponse(LineItemBase):
    id: int
    quote_id: int
    total: float

    class Config:
        orm_mode = True

class QuoteBase(BaseModel):
    client_id: int
    expiry_date: Optional[date] = None

class QuoteCreate(QuoteBase):
    line_items: List[LineItemCreate]

class QuoteUpdate(BaseModel):
    expiry_date: Optional[date] = None
    status: Optional[str] = None
    line_items: Optional[List[LineItemCreate]] = None

class QuoteResponse(QuoteBase):
    id: int
    status: str
    subtotal: float
    tax: float
    total: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    line_items: List[LineItemResponse] = []

    class Config:
        orm_mode = True