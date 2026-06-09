from __future__ import annotations

from core.invariants import InvariantSpec, check_invariant
from redteam.executable_drill import BlindObservableBundle, DrillContext, DrillPrecheck, DrillTrace, blind_feature_from_intent
from redteam.impact_assertion import ImpactAssertion
from redteam.local_tx_intent import LocalTxIntent


class ExecutableMultiStageDrill:
    drill_id = "DRILL-MULTI-STAGE-001"
    risk_type = "multi_stage_composition"
    target_protocol = "MockLendingVault"
    required_runtime = "mock"

    async def precheck(self, arena, target) -> DrillPrecheck:
        arena.safety_guard.assert_drill_allowed(self, arena, target)
        arena.bind_target(target)
        return DrillPrecheck(True)

    async def prepare(self, arena, target) -> DrillContext:
        arena.safety_guard.assert_drill_allowed(self, arena, target)
        arena.bind_target(target)
        return DrillContext(snapshot_id=arena.snapshot(), risk_hypothesis_id="RH-MULTI-001", hidden_ground_truth={"expected_action": "pause"})

    async def arm(self, arena, context: DrillContext) -> list[LocalTxIntent]:
        return [
            LocalTxIntent("mock://pool", "benign_decoy", "safe:multi-stage-decoy-1", 0, "user", "local-normal", "mock-only"),
            LocalTxIntent("mock://pool", "benign_decoy", "safe:multi-stage-decoy-2", 0, "user", "local-normal", "mock-only"),
            LocalTxIntent("mock://oracle", "oracle_divergence", "safe:multi-stage-price-reference", 0, "adversarial-researcher", "local-priority", "mock-only"),
            LocalTxIntent("mock://pool", "liquidity_shock", "safe:multi-stage-liquidity-depth", 0, "adversarial-researcher", "local-priority", "mock-only"),
            LocalTxIntent("mock://vault", "price_sensitive_withdrawal", "safe:multi-stage-vault-touch", 0, "adversarial-researcher", "local-priority", "mock-only"),
        ]

    async def trigger(self, arena, context: DrillContext) -> DrillTrace:
        trace_events = []
        for step_index, intent in enumerate(await self.arm(arena, context), start=1):
            arena.submit_pending(intent)
            trace_events.append({"event": "ordered_pending_intent", "step_index": step_index})
        return DrillTrace(self.drill_id, list(arena.pending_txs), trace_events, context.hidden_ground_truth)

    async def collect_blue_observables(self, trace: DrillTrace) -> BlindObservableBundle:
        bundle = BlindObservableBundle(
            drill_id=trace.drill_id,
            pending_features=[blind_feature_from_intent(tx) for tx in trace.tx_intents],
            state_window={"pending_count": len(trace.tx_intents), "visibility_mode": "public_local_mempool", "window_shape": "decoy_price_liquidity_vault_chain"},
        )
        bundle.assert_no_ground_truth()
        return bundle

    async def assert_impact(self, arena, trace: DrillTrace) -> ImpactAssertion:
        state = arena.get_state()
        specs = [
            InvariantSpec("INV-ORACLE-001", "mock://vault", "oracle_dependency", "oracle deviation", [], "oracle_deviation_within_threshold", "unpaused divergence", "high"),
            InvariantSpec("INV-LIQUIDITY-001", "mock://pool", "liquidity_pressure", "liquidity floor", [], "liquidity_above_floor", "pool liquidity below configured floor", "high"),
            InvariantSpec("INV-VAULT-001", "mock://vault", "vault_accounting", "vault accounting consistency", [], "vault_accounting_consistent", "liabilities exceed assets", "high"),
        ]
        failed = [spec.invariant_id for spec in specs if not check_invariant(spec, state)]
        return ImpactAssertion(
            invariant_id="INV-MULTI-STAGE-001",
            impact_success=bool(failed),
            blocked_by_blue=bool(state.get("paused")) and state.get("blocked_sensitive_actions", 0) > 0,
            state_diff={},
            notes=[f"Checked multiple invariants; failed={failed}"],
        )

    async def cleanup(self, arena, context: DrillContext) -> None:
        arena.revert(context.snapshot_id)
