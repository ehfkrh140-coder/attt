from __future__ import annotations

import pytest

from arenas.evm_fork_execution_arena import EvmForkExecutionArena, UNSUPPORTED_EXECUTABLE_FORK_DRILLS
from core.capability_boundary import (
    FORBIDDEN_OUTSIDE_MODELED_INSIDE_MATRIX,
    BlueTeamCapabilityBoundary,
    PermanentForbiddenCapability,
    ReconCapabilityBoundary,
    RedTeamCapabilityBoundary,
    assert_external_capability_forbidden,
    matrix_by_forbidden,
    validate_matrix_complete,
)
from core.containment_policy import (
    KOREAN_SEALED_LAB_PRINCIPLE,
    PUBLIC_WORLD_SIDE_EFFECTS_FORBIDDEN,
    RECON_STRONGER_THAN_RED_EN,
    RECON_STRONGER_THAN_RED_KO,
    public_world_capability_decision,
    sealed_lab_modeling_decision,
)
from evaluation.no_fake_scenario import (
    NoFakeScenarioScore,
    ScenarioMaturityLevel,
    blue_response_is_sufficient,
    evaluator_verdict_has_required_diff,
    narrative_only_recon_is_insufficient,
    red_drill_has_required_transition,
)
from recon.extreme_recon_model import (
    BlueObservableCandidate,
    EvaluatorInvariantCandidate,
    LocalDrillCandidate,
    LocalProbePlan,
    ReconEvidenceRequirement,
    ReconFinding,
    VulnerabilityClass,
)
from redteam.local_tx_intent import LocalTxIntent


def _intent() -> LocalTxIntent:
    return LocalTxIntent(
        target="manifest-scoped-target",
        function_category="design-only",
        calldata_label="sanitized-intent-label",
        value=0,
        sender_role="synthetic-local-actor",
        gas_strategy="local-only",
        safety_scope="sealed-lab-review",
    )


def test_permanent_forbidden_capabilities_remain_forbidden() -> None:
    for capability in PermanentForbiddenCapability:
        decision = public_world_capability_decision(capability)
        assert not decision.allowed
        assert not decision.phase2b_execution_enabled
        assert capability.value in decision.reason
        with pytest.raises(PermissionError, match="FORBIDDEN_OUTSIDE_SEALED_LAB"):
            assert_external_capability_forbidden(capability)


def test_each_forbidden_external_capability_has_sealed_lab_equivalent() -> None:
    assert validate_matrix_complete()
    matrix = matrix_by_forbidden()
    assert set(matrix) == set(PermanentForbiddenCapability)
    for capability, entry in matrix.items():
        assert entry.forbidden == capability
        assert entry.modeled_inside.value
        assert "Forbidden" in entry.current_phase2a_status or "forbidden" in entry.current_phase2a_status
        assert "local" in entry.future_gate.lower() or "synthetic" in entry.future_gate.lower() or "state-diff" in entry.future_gate.lower()


def test_containment_principles_are_explicit_and_do_not_enable_phase2b() -> None:
    assert "External public-world behavior is forbidden" in PUBLIC_WORLD_SIDE_EFFECTS_FORBIDDEN
    assert "maximum realism" in PUBLIC_WORLD_SIDE_EFFECTS_FORBIDDEN
    assert "외부 세계에서는 금지한다" in KOREAN_SEALED_LAB_PRINCIPLE
    assert RECON_STRONGER_THAN_RED_KO == "Red가 최강이려면 Recon은 더 최강이어야 한다."
    assert RECON_STRONGER_THAN_RED_EN == "For Red to be world-class, Recon must be stronger than Red."
    future_model = sealed_lab_modeling_decision("sealed local fork execution", phase2b_gate_open=True)
    assert not future_model.allowed
    assert not future_model.phase2b_execution_enabled


def test_role_boundaries_separate_now_future_and_forbidden() -> None:
    recon = ReconCapabilityBoundary()
    red = RedTeamCapabilityBoundary()
    blue = BlueTeamCapabilityBoundary()
    assert "ABI compatibility probing" in recon.allowed_now
    assert "snapshot/revert-controlled active probing" in recon.future_gated
    assert PermanentForbiddenCapability.PUBLIC_NETWORK_ACTIVE_PROBING in recon.forbidden
    assert "MockArena executable drills" in red.allowed_now
    assert "sealed local fork transaction execution" in red.future_gated
    assert PermanentForbiddenCapability.REAL_PRIVATE_KEY_USAGE in red.forbidden
    assert "blind observables" in blue.allowed_now
    assert "local-only canonical identity enforcement" in blue.future_gated
    assert PermanentForbiddenCapability.PUBLIC_RPC_RED_BLUE_EXECUTION in blue.forbidden


def test_narrative_only_recon_findings_are_insufficient() -> None:
    finding = ReconFinding(
        finding_id="story-only",
        vulnerability_class=VulnerabilityClass.RESIDUAL_ASSET_SURFACE,
        affected_surface="retired_pool",
        narrative_only=True,
    )
    assert not finding.is_sufficient()
    assert narrative_only_recon_is_insufficient()


def test_complete_recon_finding_is_testable_not_narrative_only() -> None:
    finding = ReconFinding(
        finding_id="canonical-identity-local-case",
        vulnerability_class=VulnerabilityClass.CANONICAL_ASSET_IDENTITY_FAILURE,
        affected_surface="manifest_scoped_retired_pool",
        invariant_at_risk="canonical LP mint must bind to pool accounting",
        local_probe_plan=LocalProbePlan(
            name="local canonical identity probe",
            local_only=True,
            manifest_scoped=True,
            expected_state_transition="synthetic identity mismatch is rejected or quarantined",
            safety_containment="sealed lab only; no public network side effects",
        ),
        local_drill_candidate=LocalDrillCandidate(
            name="ForgedLPMintRetiredPoolDrainDrill",
            local_only=True,
            invariant_pressure="canonical asset identity pressure",
            expected_state_diff="vault balance unchanged when non-canonical mint appears",
        ),
        blue_observable_candidate=BlueObservableCandidate(
            observable_type="identity_mismatch_indicator",
            blind_feature="token account mint differs from canonical LP mint registry",
        ),
        evaluator_invariant_candidate=EvaluatorInvariantCandidate(
            invariant_name="canonical_lp_burn_accounting",
            invariant_diff_check="fake LP mint accepted or rejected",
        ),
        evidence_requirement=ReconEvidenceRequirement(
            evidence_type="sanitized_state_diff",
            required_artifact="state diff and invariant diff evidence",
        ),
        safety_containment_requirement="manifest-scoped local-only simulation",
    )
    assert finding.is_sufficient()


def test_narrative_only_red_drills_are_insufficient() -> None:
    assert not red_drill_has_required_transition(
        narrative_only=True,
        state_transition=True,
        invariant_pressure=True,
    )
    assert not red_drill_has_required_transition(
        narrative_only=False,
        state_transition=False,
        invariant_pressure=True,
    )
    assert red_drill_has_required_transition(
        narrative_only=False,
        state_transition=True,
        invariant_pressure=True,
    )


def test_alert_only_blue_behavior_is_insufficient_when_action_required() -> None:
    assert not blue_response_is_sufficient(
        alert_only=True,
        block_or_quarantine_required=True,
        action_taken=False,
    )
    assert blue_response_is_sufficient(
        alert_only=False,
        block_or_quarantine_required=True,
        action_taken=True,
    )


def test_evaluator_requires_state_or_invariant_diff_evidence() -> None:
    assert not evaluator_verdict_has_required_diff(state_diff=False, invariant_diff=False)
    assert evaluator_verdict_has_required_diff(state_diff=True, invariant_diff=False)
    assert evaluator_verdict_has_required_diff(state_diff=False, invariant_diff=True)
    assert not NoFakeScenarioScore(
        affected_surface=True,
        invariant_at_risk=True,
        local_execution_or_simulation_path=True,
        expected_state_transition=True,
        blue_blind_observable=True,
        evaluator_check=False,
        evidence_requirement=True,
        safety_containment_proof=True,
    ).passes()


def test_blue_blind_observables_do_not_leak_red_labels() -> None:
    safe = BlueObservableCandidate("identity_mismatch_indicator", "non-canonical asset identity detected")
    leaked = BlueObservableCandidate("exploit_label", "red_path success_condition revealed")
    assert safe.is_blind()
    assert not leaked.is_blind()


def test_no_fake_maturity_levels_include_phase2b_target_without_enabling_it() -> None:
    assert ScenarioMaturityLevel.L0_STORY_ONLY.value.endswith("insufficient")
    assert "phase2b_target" in ScenarioMaturityLevel.L4_SEALED_FORK_SNAPSHOT_REVERT.value
    assert "long_term" in ScenarioMaturityLevel.L5_EXTERNAL_WORLD_TWIN_PRESSURE.value


def test_raydium_style_case_is_defensive_local_only_and_models_invariants() -> None:
    text = open("docs/incidents/2026-06-10_raydium_lp_mint_validation_case.md", encoding="utf-8").read()
    assert "defensive local-only simulation design case" in text
    assert "CanonicalAssetIdentityFailure" in text
    assert "ForgedLPMintRetiredPoolDrainDrill" in text
    assert "UI-hidden or retired pool status is not security" in text
    assert "fake LP mint accepted or rejected" in text
    assert "Multi-pool same-pattern findings must be evaluated as campaign risk" in text
    assert "live Raydium interaction" in text
    assert "attacker reproduction steps" in text
    assert "raw transaction details" in text
    assert "0x" not in text


def test_required_docs_contain_reframe_language() -> None:
    safety = open("docs/SAFETY_BOUNDARY_MODEL.md", encoding="utf-8").read()
    recon = open("docs/RECON_CAPABILITY_BOUNDARY.md", encoding="utf-8").read()
    red = open("docs/RED_TEAM_CAPABILITY_BOUNDARY.md", encoding="utf-8").read()
    blue = open("docs/BLUE_TEAM_CAPABILITY_BOUNDARY.md", encoding="utf-8").read()
    no_fake = open("docs/NO_FAKE_SCENARIO_STANDARD.md", encoding="utf-8").read()
    matrix = open("docs/RED_BLUE_CAPABILITY_MATRIX.md", encoding="utf-8").read()
    status = open("docs/CAPABILITY_STATUS.md", encoding="utf-8").read()
    checklist = open("docs/PHASE_2B_READINESS_CHECKLIST.md", encoding="utf-8").read()
    assert "ForbiddenOutsideModeledInsideMatrix" in safety
    assert "외부 세계에서는 금지한다" in safety
    assert "Red가 최강이려면 Recon은 더 최강이어야 한다." in safety
    assert "Recon is a first-class adversarial discovery engine" in recon
    assert "Red Team is not a story generator" in red
    assert "Blue must be powerful but blind" in blue
    assert "No drill may pass based only on narrative" in no_fake
    assert "forbidden externally and modeled internally" in matrix
    assert "Future sealed-local capabilities after explicit gates" in status
    assert "No live exploit code" in checklist


def test_phase2b_execution_remains_disabled() -> None:
    with pytest.raises(RuntimeError, match=UNSUPPORTED_EXECUTABLE_FORK_DRILLS):
        EvmForkExecutionArena().execute_local_intent(_intent())
