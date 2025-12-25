from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel

class LineItem(BaseModel):
    __tablename__ = "line_items"

    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    rate = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    quote = relationship("Quote", back_populates="line_items")
