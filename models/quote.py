from sqlalchemy import Column, Integer, Numeric, Date, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Quote(BaseModel):
    __tablename__ = "quotes"
    
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    status = Column(String(50), default="draft", nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    expiry_date = Column(Date, nullable=True)
    title = Column(String, nullable=False)

    client = relationship("Client", back_populates="quotes")
    line_items = relationship("LineItem", back_populates="quote", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="quote", uselist=False, cascade="all, delete-orphan")