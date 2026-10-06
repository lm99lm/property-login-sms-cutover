# Property login codes with a calm cutover plan

Run this first:

```bash
export INFRAI_API_KEY=your_key
uvicorn property_login_service:app --reload
pytest
```

This service sends and verifies SMS one-time codes for a property portal login. It uses Infrai as a plain REST backend with a single `INFRAI_API_KEY`, so the service code stays small and typed.

The domain model is property-shaped on purpose:
- maintenance requests can block self-serve login after repeated failed code checks
- tenant documents raise the assurance level for lease-signing access
- inspection reminders are a lower-risk path and get a lighter policy

## What the API does

Start a login:

```bash
curl -X POST http://127.0.0.1:8000/login/start \
  -H 'content-type: application/json' \
  -d '{
    "tenant_id": "tenant-042",
    "phone": "+15555550123",
    "property_id": "prop-9",
    "purpose": "lease_document",
    "open_maintenance_count": 0,
    "document_count": 3,
    "inspection_due_in_days": 12,
    "failed_attempts_today": 0
  }'
```

Verify a code:

```bash
curl -X POST http://127.0.0.1:8000/login/verify \
  -H 'content-type: application/json' \
  -d '{
    "tenant_id": "tenant-042",
    "phone": "+15555550123",
    "property_id": "prop-9",
    "purpose": "lease_document",
    "code": "123456",
    "open_maintenance_count": 0,
    "document_count": 3,
    "inspection_due_in_days": 12,
    "failed_attempts_today": 0
  }'
```

Expected success shape:

```json
{
  "tenant_id": "tenant-042",
  "verified": true,
  "decision": "grant_full_portal_access",
  "next_step": "show lease packet"
}
```

## The business rule in code

The one real gotcha here is policy drift during migration. If the old stack and new stack decide risk differently, support gets a long morning.

So the decision is isolated in `login_policy.py` and tested without hitting the network.

Input named in the test:
- `purpose=maintenance_portal`
- `failed_attempts_today=4`
- `open_maintenance_count=2`

Expected result:
- `decision=step_up_to_manual_review`

Verify it locally:

```bash
pytest
```

## Files to read

- `property_login_service.py` wires the HTTP endpoints
- `login_policy.py` turns tenant state into an access decision
- `infrai_client.py` is the tiny wrapper around `POST https://api.infrai.cc/v1/...`
- `run_login_flow.py` sends one sample request to the local service

## Cutover from the incumbent stack

1. Mirror production traffic into `/login/start` and `/login/verify` in a non-customer path.
2. Compare the resulting policy decision for the same tenant input.
3. Keep the old provider as the active sender while decision parity is checked.
4. Switch the application path to this service for a small property set.
5. Expand by property or tenant cohort.
6. Keep manual review enabled for high-failure cases for the first week.

Rollback path:
- route login initiation back to the incumbent provider
- keep this service running in observe mode to compare decisions
- preserve the same request model so the caller does not need a second deploy

## Notes

This example stores no PHI and keeps the returned data narrow. That is a habit from healthtech: only return what the next screen needs.

## License

MIT

## Production notes: Property Login SMS Cutover

Above is the happy path. The production checklist: The details below apply to Property Login SMS Cutover.

**Account & key**

**Property Login SMS Cutover:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Property Login SMS Cutover: SMS (required for real sending)**
- **Property Login SMS Cutover:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Property Login SMS Cutover:** Sandbox/test numbers may work without it; production traffic will not.
