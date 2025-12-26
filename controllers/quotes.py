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
    # Verify client belongs to same company
    client = db.query(Client).join(UserModel).filter(
        Client.id == quote.client_id, 
        UserModel.company_name == current_user.company_name
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    subtotal, tax, total = calculate_quote_totals(quote.line_items)

    new_quote = Quote(
        client_id=quote.client_id,
        expiry_date=quote.expiry_date,
        title=quote.title,
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
    quotes = db.query(Quote).join(Client).join(UserModel).filter(UserModel.company_name == current_user.company_name).all()
    return quotes

@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quote = db.query(Quote).join(Client).join(UserModel).filter(Quote.id == quote_id, UserModel.company_name == current_user.company_name).first()
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
    quote = db.query(Quote).join(Client).join(UserModel).filter(Quote.id == quote_id, UserModel.company_name == current_user.company_name).first()
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

@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quote = db.query(Quote).join(Client).join(UserModel).filter(Quote.id == quote_id, UserModel.company_name == current_user.company_name).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    db.delete(quote)
    db.commit()
    return None

@router.post("/{quote_id}/send")
def send_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    quote = db.query(Quote).join(Client).join(UserModel).filter(Quote.id == quote_id, UserModel.company_name == current_user.company_name).first()
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
    quote = db.query(Quote).join(Client).join(UserModel).filter(Quote.id == quote_id, UserModel.company_name == current_user.company_name).first()
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
    quote = db.query(Quote).join(Client).join(UserModel).filter(Quote.id == quote_id, UserModel.company_name == current_user.company_name).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    import re

    # Helper for drawing wrapped text? For now, assume simple lines.
    
    # --- HEADER ---
    # Company Info (Left)
    y = height - 50
    p.setFont("Helvetica-Bold", 16)
    company_name = current_user.company_name or "Company Name"
    p.drawString(50, y, company_name)
    y -= 20
    p.setFont("Helvetica", 10)
    p.drawString(50, y, current_user.email)
    
    # Document Info (Right)
    y_top = height - 50
    p.setFont("Helvetica-Bold", 24)
    p.drawRightString(width - 50, y_top, "QUOTE")
    
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width - 50, y_top - 30, f"#{quote.id}")
    
    p.setFont("Helvetica", 10)
    p.drawRightString(width - 50, y_top - 45, f"Date: {quote.created_at.strftime('%Y-%m-%d')}")
    if quote.expiry_date:
        p.drawRightString(width - 50, y_top - 60, f"Expires: {quote.expiry_date.strftime('%Y-%m-%d')}")

    # --- BILL TO ---
    y = height - 140
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "BILL TO:")
    y -= 15
    p.setFont("Helvetica", 12)
    p.drawString(50, y, quote.client.name)
    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(50, y, quote.client.email)
    if quote.client.phone:
        y -= 12
        p.drawString(50, y, quote.client.phone)
    if quote.client.address:
        y -= 12
        p.drawString(50, y, quote.client.address)

    # --- TITLE ---
    y -= 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, quote.title)

    # --- TABLE HEADER ---
    y -= 30
    p.setLineWidth(1)
    p.line(50, y, width - 50, y)
    y -= 15
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "DESCRIPTION")
    p.drawString(300, y, "QTY")
    p.drawString(380, y, "RATE")
    p.drawString(480, y, "AMOUNT")
    y -= 5
    p.line(50, y, width - 50, y)
    
    # --- TABLE CONTENT ---
    y -= 20
    p.setFont("Helvetica", 10)
    
    for item in quote.line_items:
         # Simple check for page break
        if y < 100:
            p.showPage()
            y = height - 50
            # Redraw headers? simplified for now just continue
        
        p.drawString(50, y, item.description)
        p.drawString(300, y, str(item.quantity))
        p.drawString(380, y, f"${item.rate:,.2f}")
        p.drawString(480, y, f"${item.total:,.2f}")
        y -= 20

    # --- TOTALS ---
    y -= 10
    p.line(300, y, width - 50, y)
    y -= 20
    
    p.setFont("Helvetica-Bold", 10)
    p.drawString(380, y, "Subtotal:")
    p.drawRightString(width - 50, y, f"${quote.subtotal:,.2f}")
    y -= 15
    
    p.drawString(380, y, "Tax (10%):")
    p.drawRightString(width - 50, y, f"${quote.tax:,.2f}")
    y -= 15
    
    p.setFillColorRGB(0.9, 0.9, 0.9) # Light gray background for total
    p.rect(370, y - 5, width - 50 - 370, 20, fill=1, stroke=0)
    p.setFillColorRGB(0, 0, 0)
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(380, y, "Total:")
    p.drawRightString(width - 50, y, f"${quote.total:,.2f}")
    
    # --- FOOTER ---
    p.setFont("Helvetica", 9)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    
    # Prepared By
    p.drawString(50, 50, f"Prepared by: {current_user.username}")
    p.drawCentredString(width / 2, 30, "Thank you for your business!")

    p.showPage()
    p.save()

    buffer.seek(0)
    
    # Filename sanitization
    safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', quote.title)
    filename = f"{safe_title}_{quote.id}.pdf"
    
    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})