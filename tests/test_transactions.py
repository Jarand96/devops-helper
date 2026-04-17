import pytest
from unittest.mock import patch, AsyncMock
from backend.models import Transaction, TransactionStatus


def make_transaction(db, **kwargs):
    defaults = dict(
        external_id="ext-001",
        amount=50.0,
        currency="USD",
        status=TransactionStatus.succeeded,
        customer_email="user@example.com",
        description="Test charge",
    )
    defaults.update(kwargs)
    tx = Transaction(**defaults)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


class TestListTransactions:
    def test_empty(self, client):
        response = client.get("/api/transactions/")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_existing(self, client, db_session):
        make_transaction(db_session)
        response = client.get("/api/transactions/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_limit(self, client, db_session):
        for i in range(5):
            make_transaction(db_session, external_id=f"ext-{i}")
        response = client.get("/api/transactions/?limit=3")
        assert len(response.json()) == 3


class TestGetTransaction:
    def test_found(self, client, db_session):
        tx = make_transaction(db_session)
        response = client.get(f"/api/transactions/{tx.id}")
        assert response.status_code == 200
        assert response.json()["external_id"] == tx.external_id

    def test_not_found(self, client):
        response = client.get("/api/transactions/99999")
        assert response.status_code == 404


class TestCreateCharge:
    @patch("backend.routers.transactions.payment.charge", new_callable=AsyncMock)
    def test_success(self, mock_charge, client):
        mock_charge.return_value = {"id": "ch_123", "status": "succeeded"}
        payload = {
            "amount": 99.99,
            "currency": "USD",
            "customer_email": "buyer@example.com",
            "description": "Order #42",
        }
        response = client.post("/api/transactions/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "succeeded"
        assert data["amount"] == 99.99

    @patch("backend.routers.transactions.payment.charge", new_callable=AsyncMock)
    def test_gateway_failure_stores_failed_status(self, mock_charge, client):
        mock_charge.side_effect = Exception("gateway timeout")
        payload = {
            "amount": 10.0,
            "currency": "USD",
            "customer_email": "buyer@example.com",
            "description": "Will fail",
        }
        response = client.post("/api/transactions/", json=payload)
        assert response.status_code == 201
        assert response.json()["status"] == "failed"

    def test_invalid_email_rejected(self, client):
        payload = {
            "amount": 10.0,
            "currency": "USD",
            "customer_email": "not-an-email",
            "description": "Bad request",
        }
        response = client.post("/api/transactions/", json=payload)
        assert response.status_code == 422


class TestRefundTransaction:
    @patch("backend.routers.transactions.payment.refund", new_callable=AsyncMock)
    def test_refund_succeeded_transaction(self, mock_refund, client, db_session):
        mock_refund.return_value = {"id": "re_123"}
        tx = make_transaction(db_session, status=TransactionStatus.succeeded)
        response = client.post(f"/api/transactions/{tx.id}/refund")
        assert response.status_code == 200
        assert response.json()["status"] == "refunded"

    def test_cannot_refund_pending(self, client, db_session):
        tx = make_transaction(
            db_session, external_id="ext-pending", status=TransactionStatus.pending
        )
        response = client.post(f"/api/transactions/{tx.id}/refund")
        assert response.status_code == 400

    def test_refund_nonexistent(self, client):
        response = client.post("/api/transactions/99999/refund")
        assert response.status_code == 404

    @patch("backend.routers.transactions.payment.refund", new_callable=AsyncMock)
    def test_gateway_error_returns_502(self, mock_refund, client, db_session):
        mock_refund.side_effect = Exception("upstream error")
        tx = make_transaction(
            db_session, external_id="ext-refund-fail", status=TransactionStatus.succeeded
        )
        response = client.post(f"/api/transactions/{tx.id}/refund")
        assert response.status_code == 502
