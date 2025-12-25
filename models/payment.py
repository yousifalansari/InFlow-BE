from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Payment(BaseModel):
    __tablename__ = "payments"

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(String(50), nullable=False) # bank, stripe, paypal, cash
    reference = Column(String(255), nullable=True) # Transaction ID etc.
    paid_at = Column(DateTime, default=func.now(), nullable=False)

    invoice = relationship("Invoice", back_populates="payments")
