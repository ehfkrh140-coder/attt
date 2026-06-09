from __future__ import annotations

import asyncio

import pytest

from arenas.local_mempool_arena import LocalMempoolArena
from arenas.mock_arena import MockArena
from blue.defender_engine import DefenderEngine
from core.errors import SafetyGuardError, ValidationError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard
from eval.evaluation_harness import EvaluationHarness
from eval.state_diff import diff_states
from recon.recon_engine import ReconEngine
from recon.target_resolver import TargetResolver
from redteam.drill_registry import ERROR_REQUIRES_EXECUTABLE_DRILL, validate_red_challenge
from redteam.drills.decoy_pressure_drill import ExecutableDecoyPressureDrill
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.executable_drill import StaticRedScenario
from redteam.local_tx_intent import LocalTxIntent
from reports.report_writer import write_safe_report
from targets.target_schema import TargetProtocolSpec, mock_target


def test_red_static_scenario_is_not_accepted():
    with pytest.raises(ValidationError, match=ERROR_REQUIRES_EXECUTABLE_DRILL):
        validate_red_challenge(StaticRedScenario("text", "only narrative"))


def test_recon_requires_target_protocol_spec():
    with pytest.raises(ValidationError, match="RECON_REQUIRES_TARGET_PROTOCOL_SPEC"):
        ReconEngine().run("DeFi")


def test_protocol_name_only_does_not_allow_drill_execution():
    report = TargetResolver().resolve_protocol_name_only("Aave", "ethereum")
    assert not report.scope_confirmed
    assert not report.executable_drills_allowed
    unconfirmed = TargetProtocolSpec("Aave", "evm", "ethereum", None, "resolver")
    assert not TargetResolver().can_execute_drills(unconfirmed)


def test_red_drill_executes_only_inside_local_arena():
    async def scenario():
        target = mock_target(scope_confirmed=True)
        arena = MockArena()
        drill = ExecutableOracleDivergenceDrill()
        assert (await drill.precheck(arena, target)).allowed

        class PublicArena(MockArena):
            rpc_url = "https://mainnet.example.invalid"
            chain_id = 1
            is_local = False

        with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
            await drill.precheck(PublicArena(), target)
    asyncio.run(scenario())


def test_red_extreme_local_drill():
    async def scenario():
        target = mock_target(scope_confirmed=True)
        arena = LocalMempoolArena()
        drill = ExecutableOracleDivergenceDrill()
        context = await drill.prepare(arena, target)
        pre = arena.get_state()
        trace = await drill.trigger(arena, context)
        assert trace.tx_intents
        assert any(tx.function_category == "benign_decoy" for tx in trace.tx_intents)
        arena.mine_pending(defense_first=False)
        post = arena.get_state()
        assert diff_states(pre, post)
        impact = await drill.assert_impact(arena, trace)
        assert impact.invariant_id == "INV-ORACLE-001"
    asyncio.run(scenario())


def test_red_drill_not_portable():
    tx = LocalTxIntent("mock://vault", "oracle_divergence", "safe:opaque-local-label", 0, "researcher", "local", "mock-only")
    report = str(tx.public_report_dict())
    assert "raw_calldata" not in report
    assert "send_raw_transaction" not in report
    assert SafetyGuard().assert_safe_report(report).allowed


def test_blue_blocks_executable_oracle_withdrawal_drill():
    async def scenario():
        target = mock_target(scope_confirmed=True)
        recon = ReconEngine().run(target)
        result = await EvaluationHarness().run(target, recon, LocalMempoolArena(), ExecutableOracleDivergenceDrill())
        assert result.blue_blocks == 1
        assert result.red_impact_successes == 0
        assert not result.label_leakage_detected
    asyncio.run(scenario())


def test_blue_handles_decoy_pressure():
    async def scenario():
        arena = LocalMempoolArena()
        drill = ExecutableDecoyPressureDrill()
        context = await drill.prepare(arena, mock_target(True))
        trace = await drill.trigger(arena, context)
        action = DefenderEngine().defend(arena, await drill.collect_blue_observables(trace))
        assert action.action_type == "monitor"
    asyncio.run(scenario())


def test_blue_cannot_access_ground_truth():
    blue_files = list(__import__("pathlib").Path("blue").glob("*.py"))
    contents = "\n".join(path.read_text() for path in blue_files)
    assert "redteam.ground_truth_store" not in contents


def test_safety_guard_blocks_public_rpc_even_for_red_drill():
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        SafetyGuard().assert_local_rpc("https://eth-mainnet.example.invalid")


def test_evaluation_uses_state_diff_not_text_labels():
    async def scenario():
        target = mock_target(scope_confirmed=True)
        recon = ReconEngine().run(target)
        result = await EvaluationHarness().run(target, recon, LocalMempoolArena(), ExecutableOracleDivergenceDrill())
        assert any("state_diff=" in note for note in result.notes)
        assert "State diffs and invariants" in result.notes[-1]
    asyncio.run(scenario())


def test_full_executable_recon_red_blue():
    async def scenario():
        target = mock_target(scope_confirmed=True)
        recon = ReconEngine().run(target)
        assert len(recon.risk_hypotheses) >= 2
        result = await EvaluationHarness().run(target, recon, LocalMempoolArena(), ExecutableOracleDivergenceDrill())
        assert result.recon_score == result.red_score == result.blue_score == result.safety_score == 1.0
        assert "raw_calldata" not in write_safe_report(result)
    asyncio.run(scenario())
