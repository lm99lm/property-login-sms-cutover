from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from infrai_client import InfraiError, infrai
from login_policy import TenantRiskContext, evaluate_login_policy

app = FastAPI(title="property-login-service")


class LoginStartRequest(TenantRiskContext):
    pass


class LoginStartResponse(BaseModel):
    tenant_id: str
    verification_started: bool
    decision_preview: str
    next_step: str
    metadata: dict | None = None


class LoginVerifyRequest(TenantRiskContext):
    code: str


class LoginVerifyResponse(BaseModel):
    tenant_id: str
    verified: bool
    decision: str
    next_step: str
    metadata: dict | None = None


@app.post("/login/start", response_model=LoginStartResponse)
def start_login(request: LoginStartRequest) -> LoginStartResponse:
    policy = evaluate_login_policy(request)
    try:
        result = infrai.sms.otp(
            {
                "to": request.phone,
                "phone": request.phone,
            },
            idempotency_key=f"login-start:{request.tenant_id}:{request.purpose.value}:{uuid4()}",
        )
    except InfraiError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "error": exc.error}) from exc

    return LoginStartResponse(
        tenant_id=request.tenant_id,
        verification_started=True,
        decision_preview=policy.decision.value,
        next_step="prompt for sms code",
        metadata=result.get("metadata"),
    )


@app.post("/login/verify", response_model=LoginVerifyResponse)
def verify_login(request: LoginVerifyRequest) -> LoginVerifyResponse:
    policy = evaluate_login_policy(request)
    try:
        result = infrai.sms.verify(
            {
                "to": request.phone,
                "phone": request.phone,
                "code": request.code,
            },
            idempotency_key=f"login-verify:{request.tenant_id}:{request.purpose.value}:{uuid4()}",
        )
    except InfraiError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "error": exc.error}) from exc

    return LoginVerifyResponse(
        tenant_id=request.tenant_id,
        verified=True,
        decision=policy.decision.value,
        next_step=policy.next_step,
        metadata=result.get("metadata"),
    )
