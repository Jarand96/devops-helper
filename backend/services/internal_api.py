import httpx
from backend.config import INTERNAL_API_ENDPOINT, INTERNAL_API_TOKEN


def _auth_headers() -> dict:
    return {
        "Authorization": INTERNAL_API_TOKEN,
        "Accept": "application/json",
    }


async def get_revenue_summary(period: str = "monthly") -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INTERNAL_API_ENDPOINT}/reports/revenue",
            params={"period": period},
            headers=_auth_headers(),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


async def get_customer_stats() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{INTERNAL_API_ENDPOINT}/reports/customers",
            headers=_auth_headers(),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


async def push_reconciliation_report(data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{INTERNAL_API_ENDPOINT}/reports/reconciliation",
            json=data,
            headers=_auth_headers(),
            timeout=20.0,
        )
        response.raise_for_status()
        return response.json()
