from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from models.invoice import Invoice
from models.quote import Quote
from models.client import Client
from models.user import UserModel
from serializers.invoice import InvoiceCreate, InvoiceResponse, InvoiceUpdate
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
    query = db.query(Invoice).join(Quote).join(Client).join(UserModel).filter(UserModel.company_name == current_user.company_name)
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    return query.all()

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).join(UserModel).filter(Invoice.id == invoice_id, UserModel.company_name == current_user.company_name).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Verify quote belongs to company
    quote = db.query(Quote).join(Client).join(UserModel).filter(Quote.id == invoice_data.quote_id, UserModel.company_name == current_user.company_name).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    if quote.invoice:
        raise HTTPException(status_code=400, detail="Invoice already exists for this quote")
    
    # Sequential Invoice Number Logic
    total_company_invoices = db.query(Invoice).join(Quote).join(Client).join(UserModel).filter(UserModel.company_name == current_user.company_name).count()
    
    total_invoices_count = db.query(Invoice).count()
    new_invoice_number = f"INV-{(total_invoices_count + 1):04d}"

    while db.query(Invoice).filter(Invoice.invoice_number == new_invoice_number).first():
        total_invoices_count += 1
        new_invoice_number = f"INV-{(total_invoices_count + 1):04d}"

    new_invoice = Invoice(
        quote_id=quote.id,
        invoice_number=new_invoice_number,
        title=invoice_data.title,
        due_date=invoice_data.due_date,
        status=invoice_data.status,
        subtotal=quote.subtotal,
        tax=quote.tax,
        total=quote.total,
        balance_due=quote.total
    )
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    return new_invoice

@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).join(UserModel).filter(Invoice.id == invoice_id, UserModel.company_name == current_user.company_name).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice_update.due_date:
        invoice.due_date = invoice_update.due_date
    if invoice_update.title:
        invoice.title = invoice_update.title
    if invoice_update.status:
        invoice.status = invoice_update.status

    db.commit()
    db.refresh(invoice)
    return invoice

@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).join(UserModel).filter(Invoice.id == invoice_id, UserModel.company_name == current_user.company_name).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db.delete(invoice)
    db.commit()
    return None

@router.post("/{invoice_id}/send")
def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).join(UserModel).filter(Invoice.id == invoice_id, UserModel.company_name == current_user.company_name).first()
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
    invoice = db.query(Invoice).join(Quote).join(Client).join(UserModel).filter(Invoice.id == invoice_id, UserModel.company_name == current_user.company_name).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    quote = invoice.quote

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    import re

    # --- HEADER ---
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
    p.drawRightString(width - 50, y_top, "INVOICE")
    
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width - 50, y_top - 30, f"#{invoice.invoice_number}")
    
    p.setFont("Helvetica", 10)
    p.drawRightString(width - 50, y_top - 45, f"Date: {invoice.created_at.strftime('%Y-%m-%d')}")
    if invoice.due_date:
        p.drawRightString(width - 50, y_top - 60, f"Due Date: {invoice.due_date}")

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
    p.drawString(50, y, invoice.title)

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
        if y < 100:
            p.showPage()
            y = height - 50
            
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
    p.drawRightString(width - 50, y, f"${invoice.subtotal:,.2f}")
    y -= 15
    p.drawString(380, y, "Tax (10%):")
    p.drawRightString(width - 50, y, f"${invoice.tax:,.2f}")
    y -= 15
    p.setFont("Helvetica-Bold", 12)
    p.drawString(380, y, "Total:")
    p.drawRightString(width - 50, y, f"${invoice.total:,.2f}")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.setFillColorRGB(0.8, 0, 0) if invoice.balance_due > 0 else p.setFillColorRGB(0, 0.6, 0)
    p.drawString(380, y, "Balance Due:")
    p.drawRightString(width - 50, y, f"${invoice.balance_due:,.2f}")
    p.setFillColorRGB(0, 0, 0)

    # --- PAYMENT HISTORY ---
    if invoice.payments:
        y -= 40
        if y < 100:
             p.showPage()
             y = height - 50

        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Payment History")
        y -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "Date")
        p.drawString(150, y, "Method")
        p.drawString(250, y, "Reference")
        p.drawString(450, y, "Amount")
        y -= 5
        p.line(50, y, 500, y)
        y -= 15
        p.setFont("Helvetica", 10)

        for payment in invoice.payments:
            p.drawString(50, y, payment.paid_at.strftime('%Y-%m-%d'))
            p.drawString(150, y, payment.method)
            p.drawString(250, y, payment.reference or "-")
            p.drawString(450, y, f"${payment.amount:,.2f}")
            y -= 15

    # --- FOOTER ---
    p.setFont("Helvetica", 9)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawString(50, 50, f"Prepared by: {current_user.username}")
    p.drawCentredString(width / 2, 30, "Thank you for your business!")

    p.showPage()
    p.save()

    buffer.seek(0)
    
    safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', invoice.title)
    filename = f"{safe_title}_{invoice.invoice_number}.pdf"
    
    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
