from __future__ import annotations

import pytest

from arenas.mock_arena import MockArena
from blue.action_planner import DefenseAction
from blue.defense_executor import execute_defense
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, PUBLIC_CHAIN_IDS, SafetyGuard
from redteam.local_tx_intent import LocalTxIntent
from targets.target_schema import mock_target


def test_safety_guard_blocks_public_chain_ids():
    guard = SafetyGuard()
    for chain_id in PUBLIC_CHAIN_IDS:
        with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
            guard.assert_local_chain(chain_id)
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        guard.assert_local_chain(777777)


def test_safety_guard_does_not_allow_chain_id_zero_by_default():
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        SafetyGuard().assert_local_chain(0)


def test_safety_guard_blocks_value_transfer():
    tx = LocalTxIntent("mock://vault", "benign_decoy", "safe:local-only", 1, "user", "local", "mock-only")
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        SafetyGuard().assert_zero_value(tx)


def test_arena_execute_blocks_value_transfer():
    arena = MockArena()
    arena.bind_target(mock_target(True))
    pre = arena.get_state()
    tx = LocalTxIntent("mock://vault", "price_sensitive_withdrawal", "safe:value-block", 1, "user", "local", "mock-only")
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        arena.execute_local_tx(tx)
    assert arena.get_state() == pre


def test_defense_executor_blocks_value_transfer():
    arena = MockArena()
    arena.bind_target(mock_target(True))
    action = DefenseAction(
        "unsafe_value_defense",
        LocalTxIntent("mock://circuit-breaker", "defense_pause", "safe:defense-pause", 1, "guardian", "local", "mock-only"),
        "unsafe non-zero value",
    )
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        execute_defense(arena, action)
    assert arena.pending_txs == []


def test_unconfirmed_target_blocks_red_drill_precheck():
    from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill

    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        import asyncio

        asyncio.run(ExecutableOracleDivergenceDrill().precheck(MockArena(), mock_target(False)))


def test_empty_scope_blocks_execution():
    target = mock_target(True)
    empty_target = type(target)(
        protocol_name=target.protocol_name,
        runtime=target.runtime,
        network_name=target.network_name,
        fork_block=target.fork_block,
        target_mode=target.target_mode,
        authorized_scope=True,
        scope_confirmed=True,
    )
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        MockArena().bind_target(empty_target)


def test_defense_executor_passes_safety_guard():
    arena = MockArena()
    arena.bind_target(mock_target(True))
    action = DefenseAction(
        "pause",
        LocalTxIntent("mock://circuit-breaker", "defense_pause", "safe:defense-pause", 0, "guardian", "local", "mock-only"),
        "safe local defense",
    )
    result = execute_defense(arena, action)
    assert result["executed"] is True
    assert len(arena.pending_txs) == 1


def test_defense_executor_does_not_execute_none_intent():
    arena = MockArena()
    result = execute_defense(arena, DefenseAction("monitor", None, "no action"))
    assert result == {"action": "monitor", "executed": False}
    assert arena.pending_txs == []
