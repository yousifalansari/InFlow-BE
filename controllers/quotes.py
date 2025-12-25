from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from models.quote import Quote
from models.line_item import LineItem
from models.client import Client
from models.user import UserModel
from serializers.quote import QuoteCreate, QuoteUpdate, QuoteResponse
from database import get_db
from dependencies.get_current_user import get_current_user
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

router = APIRouter(prefix="/quotes", tags=["Quotes"])

def calculate_quote_totals(line_items_data):
    subtotal = 0
    for item in line_items_data:
        subtotal += item.quantity * item.rate
    tax = subtotal * 0.10 # Assuming 10% tax for now, can be parameterized
    total = subtotal + tax
    return subtotal, tax, total

@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    quote: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    client = db.query(Client).filter(Client.id == quote.client_id, Client.user_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    subtotal, tax, total = calculate_quote_totals(quote.line_items)

    new_quote = Quote(
        client_id=quote.client_id,
        expiry_date=quote.expiry_date,
        subtotal=subtotal,
        tax=tax,
        total=total,
        status="draft"
    )
    db.add(new_quote)
    db.commit()
    db.refresh(new_quote)

    for item in quote.line_items:
        line_item_total = item.quantity * item.rate
        new_line_item = LineItem(
            quote_id=new_quote.id,
            description=item.description,
            quantity=item.quantity,
            rate=item.rate,
            total=line_item_total
        )
        db.add(new_line_item)
    
    db.commit()
    db.refresh(new_quote)
    return new_quote

@router.get("/", response_model=List[QuoteResponse])
def get_quotes(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quotes = db.query(Quote).join(Client).filter(Client.user_id == current_user.id).all()
    return quotes

@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quote = db.query(Quote).join(Client).filter(Quote.id == quote_id, Client.user_id == current_user.id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@router.put("/{quote_id}", response_model=QuoteResponse)
def update_quote(
    quote_id: int,
    quote_update: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quote = db.query(Quote).join(Client).filter(Quote.id == quote_id, Client.user_id == current_user.id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if quote_update.expiry_date:
        quote.expiry_date = quote_update.expiry_date
    if quote_update.status:
        quote.status = quote_update.status
    
    if quote_update.line_items is not None:
        db.query(LineItem).filter(LineItem.quote_id == quote.id).delete()
        
        subtotal, tax, total = calculate_quote_totals(quote_update.line_items)
        quote.subtotal = subtotal
        quote.tax = tax
        quote.total = total

        for item in quote_update.line_items:
            line_item_total = item.quantity * item.rate
            new_line_item = LineItem(
                quote_id=quote.id,
                description=item.description,
                quantity=item.quantity,
                rate=item.rate,
                total=line_item_total
            )
            db.add(new_line_item)

    db.commit()
    db.refresh(quote)
    return quote

@router.post("/{quote_id}/send")
def send_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quote = db.query(Quote).join(Client).filter(Quote.id == quote_id, Client.user_id == current_user.id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote.status = "sent"
    db.commit()
    return {"message": "Quote marked as sent"}

@router.post("/{quote_id}/accept")
def accept_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quote = db.query(Quote).join(Client).filter(Quote.id == quote_id, Client.user_id == current_user.id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote.status == "expired":
         raise HTTPException(status_code=400, detail="Cannot accept expired quote")

    quote.status = "accepted"
    db.commit()
    return {"message": "Quote accepted"}

@router.get("/{quote_id}/pdf")
def generate_quote_pdf(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quote = db.query(Quote).join(Client).filter(Quote.id == quote_id, Client.user_id == current_user.id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Quote #{quote.id}")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, f"Date: {quote.created_at.strftime('%Y-%m-%d')}")
    p.drawString(50, height - 90, f"Client: {quote.client.name}")

    y = height - 130
    p.drawString(50, y, "Description")
    p.drawString(300, y, "Qty")
    p.drawString(350, y, "Rate")
    p.drawString(450, y, "Total")
    
    y -= 20
    p.line(50, y+15, 500, y+15)

    for item in quote.line_items:
        p.drawString(50, y, item.description)
        p.drawString(300, y, str(item.quantity))
        p.drawString(350, y, f"${item.rate}")
        p.drawString(450, y, f"${item.total}")
        y -= 20

    y -= 20
    p.line(50, y+15, 500, y+15)
    p.drawString(350, y, "Subtotal:")
    p.drawString(450, y, f"${quote.subtotal}")
    y -= 20
    p.drawString(350, y, "Tax:")
    p.drawString(450, y, f"${quote.tax}")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, "Total:")
    p.drawString(450, y, f"${quote.total}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=quote_{quote.id}.pdf"})