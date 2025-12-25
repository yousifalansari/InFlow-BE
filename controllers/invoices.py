from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from models.invoice import Invoice
from models.quote import Quote
from models.client import Client
from models.user import UserModel
from serializers.invoice import InvoiceCreate, InvoiceResponse
from database import get_db
from dependencies.get_current_user import get_current_user
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.get("/", response_model=List[InvoiceResponse])
def get_invoices(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    status_filter: str = None
):
    query = db.query(Invoice).join(Quote).join(Client).filter(Client.user_id == current_user.id)
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    return query.all()

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).filter(Invoice.id == invoice_id, Client.user_id == current_user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Verify quote exists and belongs to user
    quote = db.query(Quote).join(Client).filter(Quote.id == invoice_data.quote_id, Client.user_id == current_user.id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Check if invoice already exists for this quote
    if quote.invoice:
        raise HTTPException(status_code=400, detail="Invoice already exists for this quote")

    # Generate Invoice Number (Simple sequential per user logic or global)
    # Ideally should be per-user, but for MVP simple unique string
    import random
    new_invoice_number = f"INV-{random.randint(1000, 9999)}" 

    new_invoice = Invoice(
        quote_id=quote.id,
        invoice_number=new_invoice_number,
        due_date=invoice_data.due_date,
        status=invoice_data.status,
        subtotal=quote.subtotal,
        tax=quote.tax,
        total=quote.total,
        balance_due=quote.total # Initially full amount
    )
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    return new_invoice

@router.post("/{invoice_id}/send")
def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).filter(Invoice.id == invoice_id, Client.user_id == current_user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = "sent"
    db.commit()
    return {"message": "Invoice marked as sent"}

@router.get("/{invoice_id}/pdf")
def generate_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).filter(Invoice.id == invoice_id, Client.user_id == current_user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    quote = invoice.quote

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Invoice #{invoice.invoice_number}")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, f"Date: {invoice.created_at.strftime('%Y-%m-%d')}")
    p.drawString(50, height - 90, f"Due Date: {invoice.due_date}")
    p.drawString(50, height - 110, f"Client: {quote.client.name}")

    # Line Items from Quote
    y = height - 150
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

    # Totals
    y -= 20
    p.line(50, y+15, 500, y+15)
    p.drawString(350, y, "Subtotal:")
    p.drawString(450, y, f"${invoice.subtotal}")
    y -= 20
    p.drawString(350, y, "Tax:")
    p.drawString(450, y, f"${invoice.tax}")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, "Total:")
    p.drawString(450, y, f"${invoice.total}")
    y -= 20
    p.drawString(350, y, "Balance Due:")
    p.drawString(450, y, f"${invoice.balance_due}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=invoice_{invoice.invoice_number}.pdf"})
