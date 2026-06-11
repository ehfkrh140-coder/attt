from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScenarioMaturityLevel(str, Enum):
    L0_STORY_ONLY = "L0_story_only_insufficient"
    L1_STATIC_FIXTURE = "L1_static_fixture_ci_only"
    L2_ABI_ACCOUNT_GRAPH_COMPATIBLE = "L2_abi_account_graph_compatible_planning"
    L3_LOCAL_STATE_TRANSITION = "L3_local_state_transition_minimum_real_evaluation"
    L4_SEALED_FORK_SNAPSHOT_REVERT = "L4_sealed_fork_snapshot_revert_phase2b_target"
    L5_EXTERNAL_WORLD_TWIN_PRESSURE = "L5_external_world_twin_pressure_long_term"


@dataclass(frozen=True)
class NoFakeScenarioScore:
    affected_surface: bool
    invariant_at_risk: bool
    local_execution_or_simulation_path: bool
    expected_state_transition: bool
    blue_blind_observable: bool
    evaluator_check: bool
    evidence_requirement: bool
    safety_containment_proof: bool

    def passes(self) -> bool:
        return all(
            (
                self.affected_surface,
                self.invariant_at_risk,
                self.local_execution_or_simulation_path,
                self.expected_state_transition,
                self.blue_blind_observable,
                self.evaluator_check,
                self.evidence_requirement,
                self.safety_containment_proof,
            )
        )


def narrative_only_recon_is_insufficient() -> bool:
    return not NoFakeScenarioScore(False, False, False, False, False, False, False, False).passes()


def evaluator_verdict_has_required_diff(*, state_diff: bool, invariant_diff: bool) -> bool:
    return state_diff or invariant_diff


def red_drill_has_required_transition(*, narrative_only: bool, state_transition: bool, invariant_pressure: bool) -> bool:
    return (not narrative_only) and state_transition and invariant_pressure


def blue_response_is_sufficient(*, alert_only: bool, block_or_quarantine_required: bool, action_taken: bool) -> bool:
    if block_or_quarantine_required and alert_only:
        return False
    if block_or_quarantine_required and not action_taken:
        return False
    return True
