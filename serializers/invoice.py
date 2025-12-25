from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class InvoiceBase(BaseModel):
    quote_id: int
    due_date: date
    status: Optional[str] = "sent"

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    invoice_number: str
    subtotal: float
    tax: float
    total: float
    balance_due: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
