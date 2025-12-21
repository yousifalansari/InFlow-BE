from pydantic import BaseModel

class QuoteSchema(BaseModel):
    client_id: int
    status: str
    subtotal: float
    tax: float
    total: float
    expiry_date: str

    class Config:
        from_attributes = True  

class QuoteResponseSchema(BaseModel):
    id: int
    client_id: int
    status: str
    subtotal: float
    tax: float
    total: float
    expiry_date: str

    class Config:
        from_attributes = True  