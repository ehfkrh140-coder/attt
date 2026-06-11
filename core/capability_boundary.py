from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PermanentForbiddenCapability(str, Enum):
    PUBLIC_NETWORK_ACTIVE_PROBING = "public_network_active_probing"
    PUBLIC_NETWORK_TRANSACTION_BROADCAST = "public_network_transaction_broadcast"
    PUBLIC_RPC_RED_BLUE_EXECUTION = "public_rpc_red_blue_execution"
    LIVE_VICTIM_TARGETING = "live_victim_targeting"
    PUBLIC_MEMPOOL_OBSERVATION_FOR_ATTACK_DISCOVERY = "public_mempool_observation_for_attack_discovery"
    REAL_PRIVATE_KEY_USAGE = "real_private_key_usage"
    REAL_FUND_MOVEMENT = "real_fund_movement"
    OUT_OF_SCOPE_CONTRACT_PROGRAM_EXPLORATION = "out_of_scope_contract_program_exploration"
    REPLAYABLE_EXPLOIT_PACKAGE_GENERATION = "replayable_exploit_package_generation"
    RAW_REUSABLE_CALLDATA_TRANSACTION_BUNDLE_OUTPUT = "raw_reusable_calldata_transaction_bundle_output"
    PUBLIC_NETWORK_PORTABLE_EXPLOIT_ARTIFACTS = "public_network_portable_exploit_artifacts"


class SealedLocalModeledCapability(str, Enum):
    LOCAL_ACTIVE_PROBING_INSIDE_SEALED_FORK_TWIN = "local_active_probing_inside_sealed_fork_twin"
    LOCAL_RPC_FORK_VALIDATOR_EXECUTION_AFTER_GATING = "local_rpc_fork_validator_execution_after_gating"
    SYNTHETIC_VICTIM_ACCOUNTS_AND_MANIFEST_SCOPED_TWINS = "synthetic_victim_accounts_and_manifest_scoped_twins"
    LOCAL_MEMPOOL_ORDERING_CONGESTION_PRIVATE_ORDERFLOW_TWINS = "local_mempool_ordering_congestion_private_orderflow_twins"
    LAB_ONLY_DETERMINISTIC_EPHEMERAL_SIGNERS_AND_IMPERSONATION = "lab_only_deterministic_ephemeral_signers_and_impersonation"
    SYNTHETIC_BALANCES_LOCAL_FORK_BALANCES_STATE_DIFF_FUNDS = "synthetic_balances_local_fork_balances_state_diff_funds"
    MANIFEST_SCOPED_ADVERSARIAL_UNIVERSE_EXPLORATION = "manifest_scoped_adversarial_universe_exploration"
    NON_PORTABLE_RED_INTENT_SPECS_AND_SANITIZED_TRACES = "non_portable_red_intent_specs_and_sanitized_traces"
    INTERNAL_ONLY_EXECUTION_TRACE_SANITIZED_EVIDENCE_OUTPUT = "internal_only_execution_trace_sanitized_evidence_output"
    STATE_DIFF_AND_INVARIANT_DIFF_EVIDENCE = "state_diff_and_invariant_diff_evidence"


@dataclass(frozen=True)
class ForbiddenOutsideModeledInsideMapping:
    forbidden: PermanentForbiddenCapability
    modeled_inside: SealedLocalModeledCapability
    current_phase2a_status: str
    future_gate: str


FORBIDDEN_OUTSIDE_MODELED_INSIDE_MATRIX: tuple[ForbiddenOutsideModeledInsideMapping, ...] = (
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.PUBLIC_NETWORK_ACTIVE_PROBING,
        SealedLocalModeledCapability.LOCAL_ACTIVE_PROBING_INSIDE_SEALED_FORK_TWIN,
        "Forbidden outside; Phase 2A permits read-only local discovery only.",
        "Snapshot/revert-controlled local active probing after sealed execution gating.",
    ),

    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.PUBLIC_NETWORK_TRANSACTION_BROADCAST,
        SealedLocalModeledCapability.LOCAL_RPC_FORK_VALIDATOR_EXECUTION_AFTER_GATING,
        "Public-network transaction broadcast is permanently forbidden.",
        "Arena-mediated sealed local fork or validator execution after explicit future gating.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.PUBLIC_RPC_RED_BLUE_EXECUTION,
        SealedLocalModeledCapability.LOCAL_RPC_FORK_VALIDATOR_EXECUTION_AFTER_GATING,
        "Forbidden outside: Red/Blue execution must not connect to public RPC.",
        "Local RPC, local fork, or local validator execution only after Phase 2B gates.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.LIVE_VICTIM_TARGETING,
        SealedLocalModeledCapability.SYNTHETIC_VICTIM_ACCOUNTS_AND_MANIFEST_SCOPED_TWINS,
        "Forbidden outside: live victims are never targets.",
        "Synthetic victim accounts and manifest-scoped protocol twins.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.PUBLIC_MEMPOOL_OBSERVATION_FOR_ATTACK_DISCOVERY,
        SealedLocalModeledCapability.LOCAL_MEMPOOL_ORDERING_CONGESTION_PRIVATE_ORDERFLOW_TWINS,
        "Forbidden outside: public mempool observation for attack discovery is forbidden.",
        "Local mempool, ordering, congestion, and private-orderflow twins.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.REAL_PRIVATE_KEY_USAGE,
        SealedLocalModeledCapability.LAB_ONLY_DETERMINISTIC_EPHEMERAL_SIGNERS_AND_IMPERSONATION,
        "Forbidden outside: real private keys are never required or stored.",
        "Lab-only deterministic ephemeral signers and local impersonation after gates.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.REAL_FUND_MOVEMENT,
        SealedLocalModeledCapability.SYNTHETIC_BALANCES_LOCAL_FORK_BALANCES_STATE_DIFF_FUNDS,
        "Forbidden outside: real funds must never move.",
        "Synthetic balances, local fork balances, and state-diff-only fund movement.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.OUT_OF_SCOPE_CONTRACT_PROGRAM_EXPLORATION,
        SealedLocalModeledCapability.MANIFEST_SCOPED_ADVERSARIAL_UNIVERSE_EXPLORATION,
        "Forbidden outside: scope escape is forbidden.",
        "Local manifest-scoped adversarial universe exploration inside the sealed lab.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.REPLAYABLE_EXPLOIT_PACKAGE_GENERATION,
        SealedLocalModeledCapability.NON_PORTABLE_RED_INTENT_SPECS_AND_SANITIZED_TRACES,
        "Forbidden outside: replayable exploit packages are forbidden outputs.",
        "Local non-portable Red intent specs and sanitized traces.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.RAW_REUSABLE_CALLDATA_TRANSACTION_BUNDLE_OUTPUT,
        SealedLocalModeledCapability.INTERNAL_ONLY_EXECUTION_TRACE_SANITIZED_EVIDENCE_OUTPUT,
        "Forbidden outside: raw reusable calldata or transaction bundle outputs are forbidden.",
        "Local internal-only execution traces with sanitized evidence output.",
    ),
    ForbiddenOutsideModeledInsideMapping(
        PermanentForbiddenCapability.PUBLIC_NETWORK_PORTABLE_EXPLOIT_ARTIFACTS,
        SealedLocalModeledCapability.STATE_DIFF_AND_INVARIANT_DIFF_EVIDENCE,
        "Forbidden outside: public-network portable exploit artifacts are forbidden.",
        "State-diff and invariant-diff evidence that is non-portable.",
    ),
)


@dataclass(frozen=True)
class ReconCapabilityBoundary:
    allowed_now: tuple[str, ...] = (
        "full local fork or local twin read access",
        "manifest-scoped graph expansion",
        "ABI compatibility probing",
        "storage/account layout inference",
        "canonical asset identity analysis",
        "reserve/vault/accounting analysis",
        "permission/authority analysis",
        "dependency staleness analysis",
        "invariant mining",
        "local-only probe planning",
        "Red drill candidate synthesis",
        "Blue observable synthesis",
        "Evaluator invariant synthesis",
    )
    future_gated: tuple[str, ...] = (
        "snapshot/revert-controlled active probing",
        "local-only transaction simulation",
        "local-only abnormal account graph construction",
        "local-only synthetic attacker account construction",
        "local-only synthetic attacker mint construction",
        "local-only dependency failure construction",
        "local-only adversarial external-world pressure discovery",
    )
    forbidden: tuple[PermanentForbiddenCapability, ...] = (
        PermanentForbiddenCapability.PUBLIC_NETWORK_ACTIVE_PROBING,
        PermanentForbiddenCapability.PUBLIC_RPC_RED_BLUE_EXECUTION,
        PermanentForbiddenCapability.PUBLIC_MEMPOOL_OBSERVATION_FOR_ATTACK_DISCOVERY,
        PermanentForbiddenCapability.LIVE_VICTIM_TARGETING,
        PermanentForbiddenCapability.OUT_OF_SCOPE_CONTRACT_PROGRAM_EXPLORATION,
        PermanentForbiddenCapability.REAL_PRIVATE_KEY_USAGE,
        PermanentForbiddenCapability.REAL_FUND_MOVEMENT,
        PermanentForbiddenCapability.REPLAYABLE_EXPLOIT_PACKAGE_GENERATION,
    )


@dataclass(frozen=True)
class RedTeamCapabilityBoundary:
    allowed_now: tuple[str, ...] = (
        "MockArena executable drills",
        "local-only Red intent modeling",
        "fixture-backed adversarial scenarios",
        "invariant-targeted local state transitions in MockArena",
    )
    future_gated: tuple[str, ...] = (
        "sealed local fork transaction execution",
        "local-only signer use",
        "local-only impersonation",
        "synthetic attacker accounts",
        "synthetic attacker mints",
        "manifest-scoped retired/stale target interaction",
        "local-only multi-pool campaigns",
        "local-only adversarial ordering",
        "local-only private orderflow simulation",
    )
    forbidden: tuple[PermanentForbiddenCapability, ...] = tuple(PermanentForbiddenCapability)


@dataclass(frozen=True)
class BlueTeamCapabilityBoundary:
    allowed_now: tuple[str, ...] = (
        "blind observables",
        "Recon risk context",
        "MockArena local block/pause/quarantine decisions",
        "local incident evidence generation",
    )
    future_gated: tuple[str, ...] = (
        "local-only dependency isolation",
        "local-only emergency governance simulation",
        "local-only risk parameter adjustment",
        "local-only vault outflow guard",
        "local-only canonical identity enforcement",
    )
    forbidden: tuple[PermanentForbiddenCapability, ...] = (
        PermanentForbiddenCapability.PUBLIC_NETWORK_TRANSACTION_BROADCAST,
        PermanentForbiddenCapability.PUBLIC_RPC_RED_BLUE_EXECUTION,
        PermanentForbiddenCapability.REAL_PRIVATE_KEY_USAGE,
        PermanentForbiddenCapability.REAL_FUND_MOVEMENT,
        PermanentForbiddenCapability.LIVE_VICTIM_TARGETING,
        PermanentForbiddenCapability.PUBLIC_MEMPOOL_OBSERVATION_FOR_ATTACK_DISCOVERY,
        PermanentForbiddenCapability.OUT_OF_SCOPE_CONTRACT_PROGRAM_EXPLORATION,
    )


def matrix_by_forbidden() -> dict[PermanentForbiddenCapability, ForbiddenOutsideModeledInsideMapping]:
    return {entry.forbidden: entry for entry in FORBIDDEN_OUTSIDE_MODELED_INSIDE_MATRIX}


def assert_external_capability_forbidden(capability: PermanentForbiddenCapability) -> None:
    if capability not in PermanentForbiddenCapability:
        raise ValueError("unknown_capability")
    raise PermissionError(f"FORBIDDEN_OUTSIDE_SEALED_LAB:{capability.value}")


def validate_matrix_complete() -> bool:
    represented = {entry.forbidden for entry in FORBIDDEN_OUTSIDE_MODELED_INSIDE_MATRIX}
    return set(PermanentForbiddenCapability).issubset(represented)
