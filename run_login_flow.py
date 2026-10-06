import json

import httpx

payload = {
    "tenant_id": "tenant-042",
    "phone": "+15555550123",
    "property_id": "prop-9",
    "purpose": "lease_document",
    "open_maintenance_count": 0,
    "document_count": 3,
    "inspection_due_in_days": 12,
    "failed_attempts_today": 0,
}

start = httpx.post("http://127.0.0.1:8000/login/start", json=payload, timeout=10.0)
print("start:")
print(json.dumps(start.json(), indent=2))

verify_payload = dict(payload)
verify_payload["code"] = "123456"
verify = httpx.post("http://127.0.0.1:8000/login/verify", json=verify_payload, timeout=10.0)
print("verify:")
print(json.dumps(verify.json(), indent=2))
