from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from redteam.impact_assertion import ImpactAssertion
from redteam.local_tx_intent import LocalTxIntent

ANSWER_LIKE_LABELS = {
    "function_category",
    "expected_action",
    "hidden_ground_truth",
    "malicious",
    "answer_key",
    "oracle_divergence",
    "price_sensitive_withdrawal",
    "vault_accounting_pressure",
    "liquidity_shock",
    "defense_pause",
}

BLIND_FEATURE_KEYS = {
    "target_category",
    "call_shape",
    "sender_profile",
    "gas_profile",
    "value_bucket",
    "timing_pattern",
    "dependency_context",
    "state_delta_hint",
    "visibility_mode",
    "local_ordering_hint",
}


@dataclass(frozen=True)
class DrillPrecheck:
    allowed: bool
    reason: str = "OK"


@dataclass
class DrillContext:
    snapshot_id: str
    risk_hypothesis_id: str
    hidden_ground_truth: dict[str, Any] = field(default_factory=dict)


@dataclass
class DrillTrace:
    drill_id: str
    tx_intents: list[LocalTxIntent]
    state_events: list[dict[str, Any]]
    hidden_ground_truth: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BlindTxFeature:
    target_category: str
    call_shape: str
    sender_profile: str
    gas_profile: str
    value_bucket: str
    timing_pattern: str
    dependency_context: list[str]
    state_delta_hint: str | None
    visibility_mode: str
    local_ordering_hint: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BlindObservableBundle:
    drill_id: str
    pending_features: list[BlindTxFeature]
    state_window: dict[str, Any]

    def assert_no_ground_truth(self) -> None:
        feature_dicts = [feature.to_dict() if isinstance(feature, BlindTxFeature) else feature for feature in self.pending_features]
        for feature in feature_dicts:
            unexpected_keys = set(feature) - BLIND_FEATURE_KEYS
            if unexpected_keys:
                raise AssertionError(f"Blue observable exposed non-blind keys: {sorted(unexpected_keys)}")
        haystack = str({"pending_features": feature_dicts, "state_window": self.state_window}).lower()
        leaked = [label for label in ANSWER_LIKE_LABELS if label in haystack]
        if leaked:
            raise AssertionError(f"Blue observable leaked answer-like labels: {leaked}")


def blind_feature_from_intent(tx: LocalTxIntent) -> BlindTxFeature:
    value_bucket = "zero" if tx.value == 0 else "non_zero"
    sender_profile = "regular_user" if tx.sender_role == "user" else "new_research_account"
    gas_profile = "local_priority" if "priority" in tx.gas_strategy else "local_normal"

    if tx.function_category == "oracle_divergence":
        return BlindTxFeature(
            target_category="price_reference_module",
            call_shape="local_state_change",
            sender_profile=sender_profile,
            gas_profile=gas_profile,
            value_bucket=value_bucket,
            timing_pattern="clustered_pending",
            dependency_context=["oracle_path"],
            state_delta_hint="price_reference_changed",
            visibility_mode="public_local_mempool",
            local_ordering_hint="priority_cluster",
        )
    if tx.function_category == "price_sensitive_withdrawal":
        return BlindTxFeature(
            target_category="price_sensitive_vault_module",
            call_shape="value_extraction_sensitive_call",
            sender_profile=sender_profile,
            gas_profile=gas_profile,
            value_bucket=value_bucket,
            timing_pattern="clustered_pending",
            dependency_context=["vault_path", "oracle_path"],
            state_delta_hint="vault_sensitive_path_touched",
            visibility_mode="public_local_mempool",
            local_ordering_hint="same_cluster_as_price_reference_change",
        )
    if tx.function_category == "vault_accounting_pressure":
        return BlindTxFeature(
            target_category="accounting_module",
            call_shape="local_state_change",
            sender_profile=sender_profile,
            gas_profile=gas_profile,
            value_bucket=value_bucket,
            timing_pattern="clustered_pending",
            dependency_context=["vault_path"],
            state_delta_hint="accounting_boundary_touched",
            visibility_mode="public_local_mempool",
            local_ordering_hint="clustered_with_sensitive_path",
        )
    if tx.function_category == "liquidity_shock":
        return BlindTxFeature(
            target_category="liquidity_module",
            call_shape="local_state_change",
            sender_profile=sender_profile,
            gas_profile=gas_profile,
            value_bucket=value_bucket,
            timing_pattern="clustered_pending",
            dependency_context=["liquidity_path"],
            state_delta_hint="liquidity_depth_changed",
            visibility_mode="public_local_mempool",
            local_ordering_hint="priority_cluster",
        )
    return BlindTxFeature(
        target_category="liquidity_module",
        call_shape="routine_local_activity",
        sender_profile="regular_user",
        gas_profile="local_normal",
        value_bucket=value_bucket,
        timing_pattern="background_noise",
        dependency_context=[],
        state_delta_hint=None,
        visibility_mode="public_local_mempool",
        local_ordering_hint=None,
    )


class ExecutableDrill(Protocol):
    drill_id: str
    risk_type: str
    target_protocol: str
    required_runtime: str

    async def precheck(self, arena: Any, target: Any) -> DrillPrecheck: ...
    async def prepare(self, arena: Any, target: Any) -> DrillContext: ...
    async def arm(self, arena: Any, context: DrillContext) -> list[LocalTxIntent]: ...
    async def trigger(self, arena: Any, context: DrillContext) -> DrillTrace: ...
    async def collect_blue_observables(self, trace: DrillTrace) -> BlindObservableBundle: ...
    async def assert_impact(self, arena: Any, trace: DrillTrace) -> ImpactAssertion: ...
    async def cleanup(self, arena: Any, context: DrillContext) -> None: ...


@dataclass(frozen=True)
class StaticRedScenario:
    title: str
    narrative: str
