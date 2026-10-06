from login_policy import AccessDecision, LoginPurpose, TenantRiskContext, evaluate_login_policy


def test_high_failure_maintenance_login_steps_up_to_manual_review() -> None:
    ctx = TenantRiskContext(
        tenant_id="tenant-7",
        phone="+15555550123",
        property_id="prop-2",
        purpose=LoginPurpose.MAINTENANCE_PORTAL,
        open_maintenance_count=2,
        document_count=0,
        inspection_due_in_days=5,
        failed_attempts_today=4,
    )

    result = evaluate_login_policy(ctx)

    assert result.decision == AccessDecision.STEP_UP_TO_MANUAL_REVIEW
    assert result.next_step == "show support contact flow"


def test_lease_document_with_tenant_documents_grants_full_access() -> None:
    ctx = TenantRiskContext(
        tenant_id="tenant-42",
        phone="+15555550124",
        property_id="prop-9",
        purpose=LoginPurpose.LEASE_DOCUMENT,
        open_maintenance_count=0,
        document_count=3,
        inspection_due_in_days=12,
        failed_attempts_today=0,
    )

    result = evaluate_login_policy(ctx)

    assert result.decision == AccessDecision.GRANT_FULL_PORTAL_ACCESS
    assert result.next_step == "show lease packet"
