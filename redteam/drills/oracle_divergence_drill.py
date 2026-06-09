from __future__ import annotations

from core.invariants import InvariantSpec, check_invariant
from redteam.executable_drill import BlindObservableBundle, DrillContext, DrillPrecheck, DrillTrace, blind_feature_from_intent
from redteam.impact_assertion import ImpactAssertion
from redteam.local_tx_intent import LocalTxIntent


class ExecutableOracleDivergenceDrill:
    drill_id = "DRILL-ORACLE-DIVERGENCE-001"
    risk_type = "oracle_dependency"
    target_protocol = "MockLendingVault"
    required_runtime = "mock"

    async def precheck(self, arena, target) -> DrillPrecheck:
        arena.safety_guard.assert_drill_allowed(self, arena, target)
        arena.bind_target(target)
        return DrillPrecheck(True)

    async def prepare(self, arena, target) -> DrillContext:
        arena.safety_guard.assert_drill_allowed(self, arena, target)
        arena.bind_target(target)
        return DrillContext(snapshot_id=arena.snapshot(), risk_hypothesis_id="RH-ORACLE-001", hidden_ground_truth={"expected_action": "pause"})

    async def arm(self, arena, context: DrillContext) -> list[LocalTxIntent]:
        return [
            LocalTxIntent("mock://pool", "benign_decoy", "safe:decoy-volume", 0, "user", "local-normal", "mock-only"),
            LocalTxIntent("mock://oracle", "oracle_divergence", "safe:oracle-divergence-probe", 0, "adversarial-researcher", "local-priority", "mock-only"),
            LocalTxIntent("mock://vault", "price_sensitive_withdrawal", "safe:price-sensitive-withdrawal", 0, "adversarial-researcher", "local-priority", "mock-only"),
        ]

    async def trigger(self, arena, context: DrillContext) -> DrillTrace:
        trace_events = []
        for intent in await self.arm(arena, context):
            arena.submit_pending(intent)
            trace_events.append({"event": "pending_intent", "category": intent.function_category})
        return DrillTrace(self.drill_id, list(arena.pending_txs), trace_events, context.hidden_ground_truth)

    async def collect_blue_observables(self, trace: DrillTrace) -> BlindObservableBundle:
        bundle = BlindObservableBundle(
            drill_id=trace.drill_id,
            pending_features=[blind_feature_from_intent(tx) for tx in trace.tx_intents],
            state_window={"pending_count": len(trace.tx_intents), "visibility_mode": "public_local_mempool"},
        )
        bundle.assert_no_ground_truth()
        return bundle

    async def assert_impact(self, arena, trace: DrillTrace) -> ImpactAssertion:
        state = arena.get_state()
        spec = InvariantSpec("INV-ORACLE-001", "mock://vault", self.risk_type, "oracle deviation", [], "oracle_deviation_within_threshold", "unpaused divergence", "high")
        invariant_ok = check_invariant(spec, state)
        return ImpactAssertion(
            invariant_id=spec.invariant_id,
            impact_success=not invariant_ok,
            blocked_by_blue=bool(state.get("paused")) and state.get("blocked_sensitive_actions", 0) > 0,
            state_diff={},
            notes=["Impact is determined by invariant state, not text labels."],
        )

    async def cleanup(self, arena, context: DrillContext) -> None:
        arena.revert(context.snapshot_id)
