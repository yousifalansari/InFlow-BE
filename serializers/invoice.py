from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class InvoiceBase(BaseModel):
    quote_id: int
    due_date: date
    title: str
    status: Optional[str] = "sent"

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    due_date: Optional[date] = None
    title: Optional[str] = None
    status: Optional[str] = None

from typing import List, Optional
from serializers.payment import PaymentResponse

class InvoiceResponse(InvoiceBase):
    id: int
    invoice_number: str
    subtotal: float
    tax: float
    total: float
    balance_due: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    payments: List[PaymentResponse] = []

    class Config:
        from_attributes = True
