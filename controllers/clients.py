from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.client import Client
from serializers.client import ClientSchema, ClientResponseSchema
from database import get_db

router = APIRouter()

@router.post("/clients", response_model=ClientResponseSchema)
def create_client(client: ClientSchema, db: Session = Depends(get_db)):
    # Check if the email already exists
    existing_client = db.query(Client).filter(Client.email == client.email).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    new_client = Client(**client.dict())
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client