from pydantic import BaseModel

class ClientSchema(BaseModel):
    name: str
    email: str
    phone: str

    class Config:
        from_attributes = True  

class ClientResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    phone: str

    class Config:
        from_attributes = True  