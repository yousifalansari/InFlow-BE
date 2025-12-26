from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from dependencies.get_current_user import get_current_user
from models.user import UserModel
from models.client import Client
from models.quote import Quote
from models.invoice import Invoice
from models.payment import Payment
import datetime

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary")
@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    today = datetime.date.today()
    first_day_of_month = today.replace(day=1)

    # 1. Revenue this month
    total_revenue_month = db.query(func.sum(Payment.amount)).join(Invoice).join(Quote).join(Client).join(UserModel).filter(
        UserModel.company_name == current_user.company_name,
        Payment.paid_at >= first_day_of_month
    ).scalar() or 0

    # 2. Outstanding Balance
    total_outstanding = db.query(func.sum(Invoice.balance_due)).join(Quote).join(Client).join(UserModel).filter(
        UserModel.company_name == current_user.company_name
    ).scalar() or 0

    # 3. Overdue Invoices Count
    overdue_count = db.query(func.count(Invoice.id)).join(Quote).join(Client).join(UserModel).filter(
        UserModel.company_name == current_user.company_name,
        Invoice.due_date < today,
        Invoice.balance_due > 0
    ).scalar() or 0

    # 4. Revenue by Month
    revenue_by_month_query = db.query(
        func.to_char(Payment.paid_at, 'YYYY-MM').label('month'),
        func.sum(Payment.amount).label('total')
    ).join(Invoice).join(Quote).join(Client).join(UserModel).filter(
        UserModel.company_name == current_user.company_name
    ).group_by('month').all()

    revenue_by_month = [{"month": row.month, "total": row.total} for row in revenue_by_month_query]

    # 5. Revenue by Client
    revenue_by_client_query = db.query(
        Client.name,
        func.sum(Payment.amount).label('total')
    ).join(Quote, Client.id == Quote.client_id).join(Invoice).join(Payment).join(UserModel).filter(
        UserModel.company_name == current_user.company_name
    ).group_by(Client.name).all()

    revenue_by_client = [{"client": row.name, "total": row.total} for row in revenue_by_client_query]

    return {
        "total_revenue_this_month": total_revenue_month,
        "total_outstanding": total_outstanding,
        "overdue_count": overdue_count,
        "revenue_by_month": revenue_by_month,
        "revenue_by_client": revenue_by_client
    }


