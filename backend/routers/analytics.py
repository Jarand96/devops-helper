from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Transaction, TransactionStatus
from backend.services.internal_api import get_revenue_summary, get_customer_stats

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def local_summary(db: Session = Depends(get_db)):
    total_volume = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == TransactionStatus.succeeded
    ).scalar() or 0.0

    count_by_status = (
        db.query(Transaction.status, func.count(Transaction.id))
        .group_by(Transaction.status)
        .all()
    )

    return {
        "total_volume_usd": round(total_volume, 2),
        "counts": {status: count for status, count in count_by_status},
    }


@router.get("/revenue")
async def revenue_report(period: str = "monthly"):
    return await get_revenue_summary(period=period)


@router.get("/customers")
async def customer_report():
    return await get_customer_stats()
