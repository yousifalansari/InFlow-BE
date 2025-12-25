from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Client(BaseModel):
    __tablename__ = "clients"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    total_billed = Column(Integer, default=0, nullable=False)

    user = relationship("UserModel", back_populates="clients")
    quotes = relationship("Quote", back_populates="client")
