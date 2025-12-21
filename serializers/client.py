from pydantic import BaseModel

class ClientSchema(BaseModel):
    name: str
    email: str
    phone: str

    class Config:
        orm_mode = True

class ClientResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    phone: str

    class Config:
        orm_mode = True