import hashlib
import hmac
import httpx
from backend.config import PAYMENT_API_KEY, WEBHOOK_SECRET

GATEWAY_BASE_URL = "https://api.paygateway.io/v1"


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {PAYMENT_API_KEY}",
        "Content-Type": "application/json",
    }


async def charge(amount: float, currency: str, customer_email: str, description: str) -> dict:
    payload = {
        "amount": int(amount * 100),  # gateway expects cents
        "currency": currency.lower(),
        "receipt_email": customer_email,
        "description": description,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_BASE_URL}/charges",
            json=payload,
            headers=_auth_headers(),
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()


async def refund(charge_id: str, amount: float | None = None) -> dict:
    payload: dict = {"charge": charge_id}
    if amount is not None:
        payload["amount"] = int(amount * 100)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_BASE_URL}/refunds",
            json=payload,
            headers=_auth_headers(),
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()


def verify_webhook_signature(payload_bytes: bytes, sig_header: str) -> bool:
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)
