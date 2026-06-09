from __future__ import annotations

import asyncio
import inspect

from arenas.base_arena import SUPPORTED_ORDERING_MODES
from arenas.local_mempool_arena import LocalMempoolArena
from blue.action_planner import DefenseAction
from eval.evaluation_harness import EvaluationHarness
from recon.recon_engine import ReconEngine
from redteam.drills.multi_stage_drill import ExecutableMultiStageDrill
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.local_tx_intent import LocalTxIntent
from targets.target_schema import mock_target


def run(coro):
    return asyncio.run(coro)


def bound_arena_with_intents() -> LocalMempoolArena:
    arena = LocalMempoolArena()
    arena.bind_target(mock_target(True))
    for tx in [
        LocalTxIntent("mock://pool", "benign_decoy", "safe:normal", 0, "user", "local-normal", "mock-only"),
        LocalTxIntent("mock://oracle", "oracle_divergence", "safe:red-priority", 0, "adversarial-researcher", "local-priority", "mock-only"),
        LocalTxIntent("mock://circuit-breaker", "defense_pause", "safe:defense", 0, "guardian", "local-defense-first", "mock-only"),
        LocalTxIntent("mock://pool", "liquidity_shock", "safe:red-priority-2", 0, "adversarial-researcher", "local-priority", "mock-only"),
        LocalTxIntent("mock://vault", "price_sensitive_withdrawal", "safe:red-vault", 0, "adversarial-researcher", "local-priority", "mock-only"),
    ]:
        arena.submit_pending(tx)
    return arena


def labels(receipts):
    return [receipt["tx"]["calldata_label"] for receipt in receipts]


def test_ordering_modes_include_red_first_and_private_orderflow():
    assert set(SUPPORTED_ORDERING_MODES) == {
        "defense_first",
        "red_first",
        "gas_priority",
        "private_orderflow",
        "randomized_seeded",
    }


def test_evaluation_does_not_default_to_defense_first_only():
    source = inspect.getsource(EvaluationHarness.run)
    assert "defense_first=True" not in source

    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        harness = EvaluationHarness()
        red_first = await harness.run(target, recon, LocalMempoolArena(), ExecutableOracleDivergenceDrill(), ordering_mode="red_first")
        gas_priority = await harness.run(target, recon, LocalMempoolArena(), ExecutableOracleDivergenceDrill(), ordering_mode="gas_priority")
        return red_first, gas_priority

    red_first, gas_priority = run(scenario())
    assert red_first.ordering_mode == "red_first"
    assert gas_priority.ordering_mode == "gas_priority"


def test_red_first_mode_records_impact_or_damage_limitation():
    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        return await EvaluationHarness().run(target, recon, LocalMempoolArena(), ExecutableOracleDivergenceDrill(), ordering_mode="red_first")

    result = run(scenario())
    assert result.ordering_mode == "red_first"
    assert result.blue_blocks == 0
    assert result.red_impact_successes == 1
    assert result.blue_score < 1.0
    assert any("damage_recorded=True" in note for note in result.notes)


def test_private_orderflow_hides_pending_features(monkeypatch):
    seen_lengths: list[int] = []

    class SpyDefender:
        def defend(self, arena, observables):
            seen_lengths.append(len(observables.pending_features))
            return DefenseAction("monitor", None, "private orderflow fallback")

    monkeypatch.setattr("eval.evaluation_harness.DefenderEngine", SpyDefender)

    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        arena = LocalMempoolArena(private_orderflow=True)
        assert arena.visible_pending_features() == []
        return await EvaluationHarness().run(target, recon, arena, ExecutableOracleDivergenceDrill(), ordering_mode="private_orderflow")

    result = run(scenario())
    assert seen_lengths == [0]
    assert result.ordering_mode == "private_orderflow"
    assert result.blue_blocks == 0


def test_blue_score_penalized_when_only_defense_first_passes():
    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        return await EvaluationHarness().run_across_ordering_modes(
            target,
            recon,
            LocalMempoolArena,
            ExecutableOracleDivergenceDrill,
            modes=["defense_first", "red_first", "private_orderflow"],
        )

    result = run(scenario())
    assert result.blue_blocks_by_mode["defense_first"] == 1
    assert result.blue_blocks_by_mode["red_first"] == 0
    assert result.blue_blocks_by_mode["private_orderflow"] == 0
    assert result.ordering_robustness_score < 1.0


def test_randomized_seeded_ordering_is_reproducible():
    first = labels(bound_arena_with_intents().mine_pending(ordering_mode="randomized_seeded", seed=1))
    second = labels(bound_arena_with_intents().mine_pending(ordering_mode="randomized_seeded", seed=1))
    different = labels(bound_arena_with_intents().mine_pending(ordering_mode="randomized_seeded", seed=2))
    assert first == second
    assert first != different


def test_gas_priority_orders_defense_and_red_deterministically():
    ordered_labels = labels(bound_arena_with_intents().mine_pending(ordering_mode="gas_priority"))
    assert ordered_labels[0] == "safe:defense"
    assert ordered_labels[-1] == "safe:normal"
    assert ordered_labels[1:4] == ["safe:red-priority", "safe:red-priority-2", "safe:red-vault"]


def test_multi_mode_evaluation_reports_per_mode_results():
    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        return await EvaluationHarness().run_across_ordering_modes(
            target,
            recon,
            LocalMempoolArena,
            ExecutableMultiStageDrill,
            seed=7,
        )

    result = run(scenario())
    assert set(result.ordering_results) == set(SUPPORTED_ORDERING_MODES)
    assert set(result.blue_blocks_by_mode) == set(SUPPORTED_ORDERING_MODES)
    assert set(result.red_impact_successes_by_mode) == set(SUPPORTED_ORDERING_MODES)
    assert 0 <= result.ordering_robustness_score <= 1.0
    assert result.modes_passed or result.modes_failed
