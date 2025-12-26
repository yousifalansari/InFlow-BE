from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

class PaymentBase(BaseModel):
    amount: Decimal
    method: str
    reference: Optional[str] = None
    payment_date: Optional[datetime] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    invoice_id: int
    paid_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
