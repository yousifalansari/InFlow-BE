from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Invoice(BaseModel):
    __tablename__ = "invoices"

    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, unique=True)
    invoice_number = Column(String, unique=True, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), default="sent", nullable=False) # sent, paid, overdue
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    balance_due = Column(Numeric(10, 2), nullable=False)

    quote = relationship("Quote", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice")
