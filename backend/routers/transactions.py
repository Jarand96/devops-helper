from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Transaction, TransactionStatus
from backend.services import payment
import uuid

router = APIRouter(prefix="/transactions", tags=["transactions"])


class ChargeRequest(BaseModel):
    amount: float
    currency: str = "USD"
    customer_email: EmailStr
    description: str


class TransactionOut(BaseModel):
    id: int
    external_id: str
    amount: float
    currency: str
    status: TransactionStatus
    customer_email: str
    description: str | None

    class Config:
        from_attributes = True


@router.get("/", response_model=list[TransactionOut])
def list_transactions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Transaction).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@router.post("/", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_charge(body: ChargeRequest, db: Session = Depends(get_db)):
    external_id = str(uuid.uuid4())
    try:
        gateway_result = await payment.charge(
            amount=body.amount,
            currency=body.currency,
            customer_email=body.customer_email,
            description=body.description,
        )
        tx_status = TransactionStatus.succeeded
        gateway_response = str(gateway_result)
    except Exception as exc:
        tx_status = TransactionStatus.failed
        gateway_response = str(exc)

    tx = Transaction(
        external_id=external_id,
        amount=body.amount,
        currency=body.currency,
        status=tx_status,
        customer_email=body.customer_email,
        description=body.description,
        gateway_response=gateway_response,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.post("/{transaction_id}/refund", response_model=TransactionOut)
async def refund_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.status != TransactionStatus.succeeded:
        raise HTTPException(status_code=400, detail="Only succeeded transactions can be refunded")
    try:
        await payment.refund(charge_id=tx.external_id)
        tx.status = TransactionStatus.refunded
        db.commit()
        db.refresh(tx)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gateway error: {exc}")
    return tx
