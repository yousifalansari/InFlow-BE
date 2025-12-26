from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.payment import Payment
from models.invoice import Invoice
from models.quote import Quote
from models.client import Client
from serializers.payment import PaymentCreate, PaymentResponse
from database import get_db
from dependencies.get_current_user import get_current_user
from models.user import UserModel
from datetime import date, datetime

router = APIRouter(prefix="", tags=["Payments"]) # Prefix handle in main or per-endpoint if needed



def recalculate_invoice_state(invoice: Invoice):
    """
    Recalculates balance due and updates status based on total payments.
    Ensures balance never exceeds total and updates status (paid/sent/overdue).
    """
    total_paid = sum(payment.amount for payment in invoice.payments)
    
    invoice.balance_due = max(invoice.total - total_paid, 0)
    
    # Status Logic
    if invoice.balance_due == 0 and invoice.total > 0:
        invoice.status = "paid"
    else:
        if invoice.status == "paid": 
             invoice.status = "sent"
        
        # Check overdue
        if invoice.due_date and invoice.due_date < date.today():
            invoice.status = "overdue"
        elif invoice.status == "overdue" and invoice.due_date and invoice.due_date >= date.today():
            invoice.status = "sent" # Unlikely unless date changed, but good safety

@router.post("/invoices/{invoice_id}/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    invoice_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).join(UserModel).filter(Invoice.id == invoice_id, UserModel.company_name == current_user.company_name).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Safety: Recalculate first to ensure balance_due is accurate
    recalculate_invoice_state(invoice)

    if payment_data.amount > invoice.balance_due:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Payment amount (${payment_data.amount}) exceeds balance due (${invoice.balance_due})"
        )

    new_payment = Payment(
        invoice_id=invoice_id,
        amount=payment_data.amount,
        method=payment_data.method,
        reference=payment_data.reference,
        paid_at=payment_data.payment_date or datetime.now()
    )
    
    db.add(new_payment)
    db.add(new_payment)
    
    invoice.balance_due -= payment_data.amount
    if invoice.balance_due <= 0:
        invoice.status = "paid"
        invoice.balance_due = 0
    else:
        # Check overdue status just in case
        if invoice.due_date and invoice.due_date < date.today():
             invoice.status = "overdue"

    db.commit()
    db.refresh(new_payment)
    return new_payment

@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    payment = db.query(Payment).join(Invoice).join(Quote).join(Client).join(UserModel).filter(Payment.id == payment_id, UserModel.company_name == current_user.company_name).first()
    if not payment:
         raise HTTPException(status_code=404, detail="Payment not found")
    
    invoice = payment.invoice
    
    # Delete payment
    db.delete(payment)
    db.flush() # Flush to update relationship/database so recalculation sees 1 less payment
    
    # Recalculate
    recalculate_invoice_state(invoice)
    
    db.commit()
    return None

@router.put("/payments/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    payment_update: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    payment = db.query(Payment).join(Invoice).join(Quote).join(Client).join(UserModel).filter(Payment.id == payment_id, UserModel.company_name == current_user.company_name).first()
    if not payment:
         raise HTTPException(status_code=404, detail="Payment not found")
    
    invoice = payment.invoice
    
    # Check if new amount will exceed balance
    
    total_paid_others = sum(p.amount for p in invoice.payments if p.id != payment_id)
    balance_pending = max(invoice.total - total_paid_others, 0)
    
    if payment_update.amount > balance_pending:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Payment amount (${payment_update.amount}) exceeds balance due (${balance_pending})"
        )

    # Proceed
    payment.amount = payment_update.amount
    payment.method = payment_update.method
    payment.reference = payment_update.reference
    if payment_update.payment_date:
        payment.paid_at = payment_update.payment_date

    db.flush() # Update DB
    recalculate_invoice_state(invoice) # Update Invoice based on new state

    db.commit()
    db.refresh(payment)
    return payment
