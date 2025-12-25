from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

class PaymentBase(BaseModel):
    amount: Decimal
    method: str
    reference: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    invoice_id: int
    paid_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
