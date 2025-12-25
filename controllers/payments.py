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
from datetime import date

router = APIRouter(prefix="", tags=["Payments"]) # Prefix handle in main or per-endpoint if needed

# Requirements said "/invoices/{id}/payments" or just "/payments"
# Let's support POST /invoices/{id}/payments to record payment
# and DELETE /payments/{id}

@router.post("/invoices/{invoice_id}/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    invoice_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    invoice = db.query(Invoice).join(Quote).join(Client).filter(Invoice.id == invoice_id, Client.user_id == current_user.id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    new_payment = Payment(
        invoice_id=invoice_id,
        amount=payment_data.amount,
        method=payment_data.method,
        reference=payment_data.reference
    )
    
    # Update Invoice Balance
    # Balance due = Total - Sum(Payments)
    # We can just subtract the new amount
    
    if invoice.balance_due < payment_data.amount:
        # Optional: Prevent overpayment? Or allow negative balance?
        # Let's allow but maybe warn or just handle it. 
        pass 

    invoice.balance_due -= payment_data.amount
    
    # Update Status
    if invoice.balance_due <= 0:
        invoice.status = "paid"
        invoice.balance_due = 0 # Prevent negative if overpaid?
    else:
        # Check overdue? Not strictly needed here, usually done via background job or on read.
        # But if partial payment, stays as sent or partial? Requirement said: "if 0, set invoice status to paid"
        # "If due date < today and balance_due > 0, status should be overdue."
        pass

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    payment = db.query(Payment).join(Invoice).join(Quote).join(Client).filter(Payment.id == payment_id, Client.user_id == current_user.id).first()
    if not payment:
         raise HTTPException(status_code=404, detail="Payment not found")
    
    invoice = payment.invoice
    
    # Revert balance
    invoice.balance_due += payment.amount
    
    # Revert status if it was paid
    if invoice.status == "paid" and invoice.balance_due > 0:
        if invoice.due_date < date.today():
             invoice.status = "overdue"
        else:
             invoice.status = "sent"

    db.delete(payment)
    db.commit()
    return None
