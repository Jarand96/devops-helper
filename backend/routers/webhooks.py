import json
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import WebhookEvent, Transaction, TransactionStatus
from backend.services.payment import verify_webhook_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/payment")
async def receive_payment_webhook(
    request: Request,
    x_gateway_signature: str = Header(...),
    db: Session = Depends(get_db),
):
    body = await request.body()

    if not verify_webhook_signature(body, x_gateway_signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Malformed JSON payload")

    event_id = data.get("id", "")
    event_type = data.get("type", "unknown")

    if db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first():
        return {"status": "duplicate", "event_id": event_id}

    event = WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        payload=body.decode(),
        verified=1,
    )
    db.add(event)

    # Sync transaction status from webhook
    if event_type in ("charge.succeeded", "charge.failed", "charge.refunded"):
        charge_id = data.get("data", {}).get("object", {}).get("id")
        if charge_id:
            tx = db.query(Transaction).filter(Transaction.external_id == charge_id).first()
            if tx:
                status_map = {
                    "charge.succeeded": TransactionStatus.succeeded,
                    "charge.failed": TransactionStatus.failed,
                    "charge.refunded": TransactionStatus.refunded,
                }
                tx.status = status_map[event_type]

    db.commit()
    return {"status": "ok", "event_id": event_id}
