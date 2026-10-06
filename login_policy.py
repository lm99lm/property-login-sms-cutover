from enum import Enum

from pydantic import BaseModel


class LoginPurpose(str, Enum):
    MAINTENANCE_PORTAL = "maintenance_portal"
    LEASE_DOCUMENT = "lease_document"
    INSPECTION_REMINDER = "inspection_reminder"


class AccessDecision(str, Enum):
    GRANT_FULL_PORTAL_ACCESS = "grant_full_portal_access"
    GRANT_LIMITED_MAINTENANCE_ACCESS = "grant_limited_maintenance_access"
    GRANT_INSPECTION_CONFIRMATION_ONLY = "grant_inspection_confirmation_only"
    STEP_UP_TO_MANUAL_REVIEW = "step_up_to_manual_review"


class TenantRiskContext(BaseModel):
    tenant_id: str
    phone: str
    property_id: str
    purpose: LoginPurpose
    open_maintenance_count: int
    document_count: int
    inspection_due_in_days: int
    failed_attempts_today: int


class PolicyOutcome(BaseModel):
    decision: AccessDecision
    next_step: str
    assurance_level: str


def evaluate_login_policy(ctx: TenantRiskContext) -> PolicyOutcome:
    if ctx.failed_attempts_today >= 4:
        return PolicyOutcome(
            decision=AccessDecision.STEP_UP_TO_MANUAL_REVIEW,
            next_step="show support contact flow",
            assurance_level="manual",
        )

    if ctx.purpose == LoginPurpose.INSPECTION_REMINDER:
        return PolicyOutcome(
            decision=AccessDecision.GRANT_INSPECTION_CONFIRMATION_ONLY,
            next_step="show inspection reminder confirmation",
            assurance_level="otp",
        )

    if ctx.purpose == LoginPurpose.LEASE_DOCUMENT and ctx.document_count >= 1:
        return PolicyOutcome(
            decision=AccessDecision.GRANT_FULL_PORTAL_ACCESS,
            next_step="show lease packet",
            assurance_level="otp+tenant-record",
        )

    if ctx.purpose == LoginPurpose.MAINTENANCE_PORTAL and ctx.open_maintenance_count >= 1:
        return PolicyOutcome(
            decision=AccessDecision.GRANT_LIMITED_MAINTENANCE_ACCESS,
            next_step="show active maintenance requests",
            assurance_level="otp",
        )

    return PolicyOutcome(
        decision=AccessDecision.GRANT_FULL_PORTAL_ACCESS,
        next_step="show tenant dashboard",
        assurance_level="otp",
    )
