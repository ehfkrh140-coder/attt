from __future__ import annotations

import asyncio

from arenas.local_mempool_arena import LocalMempoolArena
from blue.action_planner import plan_action
from blue.context import DefenderContext
from blue.defender_engine import DefenderEngine
from blue.threat_classifier import ThreatFinding, classify
from eval.evaluation_harness import EvaluationHarness
from recon.recon_engine import ReconEngine
from redteam.drills.decoy_pressure_drill import ExecutableDecoyPressureDrill
from redteam.drills.multi_stage_drill import ExecutableMultiStageDrill
from redteam.executable_drill import BlindObservableBundle, BlindTxFeature
from targets.target_schema import mock_target


def run(coro):
    return asyncio.run(coro)


def recon_context(state: dict[str, object] | None = None, visibility_mode: str = "public_local_mempool") -> DefenderContext:
    report = ReconEngine().run(mock_target(True))
    return DefenderContext.from_inputs(
        recon_report=report,
        ordering_mode="defense_first",
        visibility_mode=visibility_mode,
        current_state=state or {},
        recent_state_window={"visibility_mode": visibility_mode},
        pending_feature_count=0,
    )


def feature(**overrides) -> dict[str, object]:
    base = {
        "target_category": "price_reference_module",
        "call_shape": "local_state_change",
        "sender_profile": "new_research_account",
        "gas_profile": "local_priority",
        "value_bucket": "zero",
        "timing_pattern": "clustered_pending",
        "dependency_context": ["oracle_path"],
        "state_delta_hint": "price_reference_changed",
        "visibility_mode": "public_local_mempool",
        "local_ordering_hint": "priority_cluster",
    }
    base.update(overrides)
    return base


def test_blue_uses_recon_context_for_oracle_vault_risk():
    state = {"oracle_price": 109.0, "pool_price": 100.0, "max_oracle_deviation": 0.10}
    features = [
        feature(),
        feature(
            target_category="price_sensitive_vault_module",
            call_shape="value_extraction_sensitive_call",
            dependency_context=["vault_path", "oracle_path"],
            state_delta_hint="vault_sensitive_path_touched",
        ),
    ]
    finding = classify(features, state, recon_context(state))
    assert finding.risk_type == "local_invariant_pressure"
    assert finding.confidence >= 0.8


def test_blue_uses_state_for_liquidity_pressure():
    state = {"pool_liquidity": 50.0, "min_pool_liquidity": 100.0}
    features = [
        feature(
            target_category="liquidity_module",
            dependency_context=["liquidity_path"],
            state_delta_hint="liquidity_depth_changed",
        )
    ]
    finding = classify(features, state, recon_context(state))
    assert finding.risk_type == "liquidity_pressure"
    assert finding.confidence >= 0.9


def test_blue_uses_state_for_vault_accounting_pressure():
    state = {"vault_assets": 100.0, "vault_liabilities": 120.0}
    features = [
        feature(
            target_category="accounting_module",
            dependency_context=["vault_path"],
            state_delta_hint="accounting_boundary_touched",
        )
    ]
    finding = classify(features, state, recon_context(state))
    assert finding.risk_type == "vault_accounting_pressure"
    assert finding.confidence >= 0.9


def test_blue_detects_multi_stage_composition_with_recon_context():
    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        arena = LocalMempoolArena()
        drill = ExecutableMultiStageDrill()
        context = await drill.prepare(arena, target)
        trace = await drill.trigger(arena, context)
        return DefenderEngine().defend(arena, await drill.collect_blue_observables(trace), recon_report=recon)

    action = run(scenario())
    assert action.action_type == "pause_price_sensitive_actions"
    assert "oracle" in action.rationale.lower() and "liquidity" in action.rationale.lower()


def test_blue_does_not_pause_on_single_weak_signal():
    arena = LocalMempoolArena()
    bundle = BlindObservableBundle(
        drill_id="weak-signal",
        pending_features=[
            BlindTxFeature(
                target_category="price_reference_module",
                call_shape="local_state_change",
                sender_profile="new_research_account",
                gas_profile="local_priority",
                value_bucket="zero",
                timing_pattern="single_pending",
                dependency_context=["oracle_path"],
                state_delta_hint="price_reference_changed",
                visibility_mode="public_local_mempool",
                local_ordering_hint=None,
            )
        ],
        state_window={"visibility_mode": "public_local_mempool"},
    )
    action = DefenderEngine().defend(arena, bundle, recon_report=ReconEngine().run(mock_target(True)))
    assert action.action_type == "monitor"


def test_blue_does_not_pause_on_decoy_only():
    async def scenario():
        arena = LocalMempoolArena()
        drill = ExecutableDecoyPressureDrill()
        context = await drill.prepare(arena, mock_target(True))
        trace = await drill.trigger(arena, context)
        return DefenderEngine().defend(arena, await drill.collect_blue_observables(trace), recon_report=ReconEngine().run(mock_target(True)))

    assert run(scenario()).action_type == "monitor"


def test_blue_private_orderflow_state_fallback():
    arena = LocalMempoolArena(private_orderflow=True)
    arena.state["oracle_price"] = 150.0
    arena.state["pool_price"] = 100.0
    bundle = BlindObservableBundle(
        drill_id="private-state-risk",
        pending_features=[],
        state_window={"visibility_mode": "private_orderflow"},
    )
    action = DefenderEngine().defend(arena, bundle, recon_report=ReconEngine().run(mock_target(True)), ordering_mode="private_orderflow")
    assert action.action_type == "alert_only"
    assert action.intent is None


def test_action_planner_uses_risk_type_not_confidence_only():
    assert plan_action(ThreatFinding("liquidity_pressure", 0.91, "liquidity", "high")).action_type == "pause_withdrawals"
    assert plan_action(ThreatFinding("vault_accounting_pressure", 0.90, "vault", "high")).action_type == "pause_vault"
    assert plan_action(ThreatFinding("private_orderflow_state_risk", 0.95, "private", "high")).action_type == "alert_only"
    assert plan_action(ThreatFinding("benign_local_noise", 0.99, "noise", "low")).action_type == "monitor"


def test_evaluation_passes_recon_context_to_blue(monkeypatch):
    calls: list[dict[str, object]] = []

    class SpyDefender:
        def defend(self, arena, observables, recon_report=None, ordering_mode="defense_first"):
            calls.append({"has_recon": recon_report is not None, "ordering_mode": ordering_mode})
            return DefenderEngine().defend(arena, observables, recon_report=recon_report, ordering_mode=ordering_mode)

    monkeypatch.setattr("eval.evaluation_harness.DefenderEngine", SpyDefender)

    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        return await EvaluationHarness().run(target, recon, LocalMempoolArena(), ExecutableMultiStageDrill(), ordering_mode="gas_priority")

    run(scenario())
    assert calls == [{"has_recon": True, "ordering_mode": "gas_priority"}]
