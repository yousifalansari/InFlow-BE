from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.quote import Quote
from serializers.quote import QuoteSchema, QuoteResponseSchema
from database import get_db

router = APIRouter()

@router.post("/quotes", response_model=QuoteResponseSchema)
def create_quote(quote: QuoteSchema, db: Session = Depends(get_db)):
    new_quote = Quote(**quote.dict())
    db.add(new_quote)
    db.commit()
    db.refresh(new_quote)
    return new_quote

@router.get("/quotes")
def get_quotes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    quotes = db.query(Quote).offset(skip).limit(limit).all()
    return 

@router.get("/quotes/{quote_id}", response_model=QuoteResponseSchema)
def get_quote(quote_id: int, db: Session = Depends(get_db)):
    quote = db.query(Quote).get(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@router.get("/quotes/client/{client_id}")
def get_quotes_by_client(client_id: int, db: Session = Depends(get_db)):
    return db.query(Quote).filter_by(client_id=client_id).all()

@router.put("/quotes/{quote_id}", response_model=QuoteResponseSchema)
def update_quote(quote_id: int, quote: QuoteSchema, db: Session = Depends(get_db)):
    db_quote = db.query(Quote).get(quote_id)
    if not db_quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    for key, value in quote.dict().items():
        setattr(db_quote, key, value)
    
    db.commit()
    db.refresh(db_quote)
    return db_quote

@router.delete("/quotes/{quote_id}")
def delete_quote(quote_id: int, db: Session = Depends(get_db)):
    quote = db.query(Quote).get(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    db.delete(quote)
    db.commit()
    return {"message": "Quote deleted successfully"}