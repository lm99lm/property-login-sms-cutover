from fastapi.testclient import TestClient

import property_login_service
from infrai_client import InfraiClient


class FakeSmsNamespace:
    def otp(self, payload, idempotency_key=None):
        assert payload == {"to": "+15555550123", "phone": "+15555550123"}
        assert idempotency_key.startswith("login-start:tenant-042:lease_document:")
        return {"ok": True, "data": {"sent": True}, "error": None, "metadata": {"provider": "test"}}

    def verify(self, payload, idempotency_key=None):
        assert payload == {"to": "+15555550123", "phone": "+15555550123", "code": "123456"}
        assert idempotency_key.startswith("login-verify:tenant-042:lease_document:")
        return {"ok": True, "data": {"verified": True}, "error": None, "metadata": {"provider": "test"}}


class FakeInfraiClient(InfraiClient):
    @property
    def sms(self):
        return FakeSmsNamespace()


def test_login_flow_maps_domain_decision_to_api_response(monkeypatch) -> None:
    monkeypatch.setattr(property_login_service, "infrai", FakeInfraiClient(api_key="test-key"))
    client = TestClient(property_login_service.app)

    start_payload = {
        "tenant_id": "tenant-042",
        "phone": "+15555550123",
        "property_id": "prop-9",
        "purpose": "lease_document",
        "open_maintenance_count": 0,
        "document_count": 3,
        "inspection_due_in_days": 12,
        "failed_attempts_today": 0,
    }
    start_response = client.post("/login/start", json=start_payload)
    assert start_response.status_code == 200
    assert start_response.json()["decision_preview"] == "grant_full_portal_access"

    verify_payload = dict(start_payload)
    verify_payload["code"] = "123456"
    verify_response = client.post("/login/verify", json=verify_payload)
    assert verify_response.status_code == 200
    assert verify_response.json() == {
        "tenant_id": "tenant-042",
        "verified": True,
        "decision": "grant_full_portal_access",
        "next_step": "show lease packet",
        "metadata": {"provider": "test"},
    }
