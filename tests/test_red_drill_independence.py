from __future__ import annotations

import asyncio
from types import MethodType

import pytest

from arenas.local_mempool_arena import LocalMempoolArena
from blue.defender_engine import DefenderEngine
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD
from eval.evaluation_harness import EvaluationHarness
from recon.recon_engine import ReconEngine
from redteam.drills.decoy_pressure_drill import ExecutableDecoyPressureDrill
from redteam.drills.liquidity_shock_drill import ExecutableLiquidityShockDrill
from redteam.drills.multi_stage_drill import ExecutableMultiStageDrill
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.drills.vault_accounting_drill import ExecutableVaultAccountingDrill
from redteam.executable_drill import ANSWER_LIKE_LABELS, BlindTxFeature
from redteam.local_tx_intent import LocalTxIntent
from targets.target_schema import TargetProtocolSpec, mock_target

DRILL_CLASSES = [ExecutableLiquidityShockDrill, ExecutableVaultAccountingDrill, ExecutableMultiStageDrill]
ANSWER_LABELS = ANSWER_LIKE_LABELS | {"calldata_label"}


def target_without(address: str) -> TargetProtocolSpec:
    target = mock_target(True)
    return TargetProtocolSpec(
        protocol_name=target.protocol_name,
        runtime=target.runtime,
        network_name=target.network_name,
        fork_block=target.fork_block,
        target_mode=target.target_mode,
        deployment_sources=target.deployment_sources,
        in_scope_contracts=[contract for contract in target.in_scope_contracts if contract["address"] != address],
        critical_assets=target.critical_assets,
        oracle_sources=target.oracle_sources,
        dex_dependencies=target.dex_dependencies,
        governance_contracts=target.governance_contracts,
        admin_roles=target.admin_roles,
        authorized_scope=True,
        scope_confirmed=True,
    )


def run(coro):
    return asyncio.run(coro)


async def collect_bundle(drill):
    arena = LocalMempoolArena()
    context = await drill.prepare(arena, mock_target(True))
    trace = await drill.trigger(arena, context)
    return await drill.collect_blue_observables(trace)


async def unblocked_impact(drill):
    arena = LocalMempoolArena()
    context = await drill.prepare(arena, mock_target(True))
    trace = await drill.trigger(arena, context)
    arena.mine_pending(defense_first=False)
    return arena, trace, await drill.assert_impact(arena, trace)


def assert_blind(bundle):
    bundle.assert_no_ground_truth()
    text = str({
        "pending_features": [feature.to_dict() for feature in bundle.pending_features],
        "state_window": bundle.state_window,
    }).lower()
    assert not any(label in text for label in ANSWER_LABELS)
    assert all(isinstance(feature, BlindTxFeature) for feature in bundle.pending_features)
    assert all("function_category" not in feature.to_dict() for feature in bundle.pending_features)


def test_red_drills_are_not_only_id_changed_subclasses():
    required_overrides = {"arm", "trigger", "collect_blue_observables", "assert_impact"}
    for drill_cls in DRILL_CLASSES:
        assert not issubclass(drill_cls, ExecutableOracleDivergenceDrill)
        assert required_overrides <= set(drill_cls.__dict__)


def test_each_drill_has_unique_impact_assertion():
    impacts = {drill_cls.__name__: run(unblocked_impact(drill_cls()))[2] for drill_cls in DRILL_CLASSES}
    assert impacts["ExecutableLiquidityShockDrill"].invariant_id == "INV-LIQUIDITY-001"
    assert impacts["ExecutableVaultAccountingDrill"].invariant_id == "INV-VAULT-001"
    assert impacts["ExecutableMultiStageDrill"].invariant_id == "INV-MULTI-STAGE-001"
    assert len({impact.invariant_id for impact in impacts.values()}) == 3


def test_liquidity_shock_drill_changes_liquidity_invariant():
    arena, _trace, impact = run(unblocked_impact(ExecutableLiquidityShockDrill()))
    state = arena.get_state()
    assert state["pool_liquidity"] < state["min_pool_liquidity"]
    assert impact.invariant_id == "INV-LIQUIDITY-001"
    assert impact.impact_success is True


def test_vault_accounting_drill_uses_vault_invariant_not_oracle_invariant():
    arena, _trace, impact = run(unblocked_impact(ExecutableVaultAccountingDrill()))
    state = arena.get_state()
    assert state["vault_liabilities"] > state["vault_assets"]
    assert impact.invariant_id == "INV-VAULT-001"
    assert impact.invariant_id != "INV-ORACLE-001"
    assert impact.impact_success is True


def test_multi_stage_drill_has_multiple_ordered_steps():
    drill = ExecutableMultiStageDrill()
    arena = LocalMempoolArena()
    context = run(drill.prepare(arena, mock_target(True)))
    trace = run(drill.trigger(arena, context))
    assert len(trace.tx_intents) >= 5
    assert [event["step_index"] for event in trace.state_events] == list(range(1, len(trace.tx_intents) + 1))
    _arena, _trace, impact = run(unblocked_impact(ExecutableMultiStageDrill()))
    assert impact.invariant_id == "INV-MULTI-STAGE-001"
    assert "INV-ORACLE-001" in impact.notes[0]
    assert "INV-LIQUIDITY-001" in impact.notes[0]


@pytest.mark.parametrize("drill", [ExecutableLiquidityShockDrill(), ExecutableVaultAccountingDrill(), ExecutableMultiStageDrill()])
def test_new_drill_blue_observables_are_blind(drill):
    assert_blind(run(collect_bundle(drill)))


def test_liquidity_drill_blue_observables_are_blind():
    assert_blind(run(collect_bundle(ExecutableLiquidityShockDrill())))


def test_vault_drill_blue_observables_are_blind():
    assert_blind(run(collect_bundle(ExecutableVaultAccountingDrill())))


def test_multi_stage_drill_blue_observables_are_blind():
    assert_blind(run(collect_bundle(ExecutableMultiStageDrill())))


@pytest.mark.parametrize(
    "drill_cls",
    [ExecutableLiquidityShockDrill, ExecutableVaultAccountingDrill, ExecutableMultiStageDrill],
)
def test_blue_detects_new_drills_using_blind_features(drill_cls):
    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        return await EvaluationHarness().run(target, recon, LocalMempoolArena(), drill_cls())

    result = run(scenario())
    assert result.blue_blocks == 1
    assert result.red_impact_successes == 0
    assert result.action_correctness == 1.0


def test_blue_detects_liquidity_shock_using_blind_features():
    test_blue_detects_new_drills_using_blind_features(ExecutableLiquidityShockDrill)


def test_blue_detects_vault_accounting_pressure_using_blind_features():
    test_blue_detects_new_drills_using_blind_features(ExecutableVaultAccountingDrill)


def test_blue_detects_multi_stage_chain_using_blind_features():
    test_blue_detects_new_drills_using_blind_features(ExecutableMultiStageDrill)


def test_decoy_only_still_monitor():
    async def scenario():
        arena = LocalMempoolArena()
        drill = ExecutableDecoyPressureDrill()
        context = await drill.prepare(arena, mock_target(True))
        trace = await drill.trigger(arena, context)
        return DefenderEngine().defend(arena, await drill.collect_blue_observables(trace))

    assert run(scenario()).action_type == "monitor"


@pytest.mark.parametrize("drill_cls", DRILL_CLASSES)
def test_new_drills_respect_safety_guard(drill_cls):
    assert run(drill_cls().precheck(LocalMempoolArena(), mock_target(True))).allowed


@pytest.mark.parametrize("drill_cls", DRILL_CLASSES)
def test_new_drills_reject_out_of_scope_target(drill_cls):
    async def scenario():
        drill = drill_cls()
        arena = LocalMempoolArena()
        context = await drill.prepare(arena, target_without("mock://pool"))
        with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
            await drill.trigger(arena, context)

    run(scenario())


@pytest.mark.parametrize("drill_cls", DRILL_CLASSES)
def test_new_drills_reject_nonzero_value_if_attempted(drill_cls):
    async def unsafe_arm(self, arena, context):
        return [LocalTxIntent("mock://pool", "benign_decoy", "safe:nonzero-attempt", 1, "user", "local-normal", "mock-only")]

    async def scenario():
        drill = drill_cls()
        drill.arm = MethodType(unsafe_arm, drill)
        arena = LocalMempoolArena()
        context = await drill.prepare(arena, mock_target(True))
        with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
            await drill.trigger(arena, context)
        assert arena.pending_txs == []

    run(scenario())
