from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.client import Client
from serializers.client import ClientSchema, ClientResponseSchema
from database import get_db

router = APIRouter()

@router.post("/clients", response_model=ClientResponseSchema)
def create_client(client: ClientSchema, db: Session = Depends(get_db)):
    existing_client = db.query(Client).filter(Client.email == client.email).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    new_client = Client(**client.dict())
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client

@router.get("/clients")
def get_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clients = db.query(Client).offset(skip).limit(limit).all()
    return clients

@router.get("/clients/{client_id}", response_model=ClientResponseSchema)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).get(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client