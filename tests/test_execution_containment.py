from __future__ import annotations

import asyncio

import pytest

from arenas.local_mempool_arena import LocalMempoolArena
from arenas.mock_arena import MockArena
from blue.action_planner import DefenseAction
from blue.defense_executor import execute_defense
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.local_tx_intent import LocalTxIntent
from targets.target_schema import TargetProtocolSpec, mock_target


def target_without(address: str) -> TargetProtocolSpec:
    target = mock_target(True)
    return TargetProtocolSpec(
        protocol_name=target.protocol_name,
        runtime=target.runtime,
        network_name=target.network_name,
        fork_block=target.fork_block,
        target_mode=target.target_mode,
        deployment_sources=target.deployment_sources,
        in_scope_contracts=[c for c in target.in_scope_contracts if c["address"] != address],
        critical_assets=target.critical_assets,
        oracle_sources=target.oracle_sources,
        dex_dependencies=target.dex_dependencies,
        governance_contracts=target.governance_contracts,
        admin_roles=target.admin_roles,
        authorized_scope=True,
        scope_confirmed=True,
    )


def test_arena_execute_rejects_out_of_scope_target():
    arena = MockArena()
    arena.bind_target(target_without("mock://vault"))
    pre = arena.get_state()
    tx = LocalTxIntent("mock://vault", "price_sensitive_withdrawal", "safe:withdrawal", 0, "user", "local", "mock-only")
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        arena.execute_local_tx(tx)
    assert arena.get_state() == pre


def test_red_drill_rejects_out_of_scope_intent():
    async def scenario():
        arena = LocalMempoolArena()
        drill = ExecutableOracleDivergenceDrill()
        target = target_without("mock://pool")
        context = await drill.prepare(arena, target)
        pre = arena.get_state()
        with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
            await drill.trigger(arena, context)
        assert arena.get_state() == pre
        assert arena.pending_txs == []

    asyncio.run(scenario())


def test_blue_defense_rejects_out_of_scope_intent():
    arena = MockArena()
    arena.bind_target(target_without("mock://circuit-breaker"))
    pre = arena.get_state()
    action = DefenseAction(
        "pause",
        LocalTxIntent("mock://circuit-breaker", "defense_pause", "safe:defense-pause", 0, "guardian", "local", "mock-only"),
        "out of scope defense target",
    )
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        execute_defense(arena, action)
    assert arena.pending_txs == []
    assert arena.get_state() == pre


def test_defense_executor_blocks_out_of_scope_action():
    test_blue_defense_rejects_out_of_scope_intent()


def test_defense_executor_does_not_submit_unsafe_intent():
    arena = MockArena()
    arena.bind_target(mock_target(True))
    unsafe = DefenseAction(
        "pause",
        LocalTxIntent("mock://outside", "defense_pause", "safe:defense-pause", 0, "guardian", "local", "mock-only"),
        "unsafe target",
    )
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        execute_defense(arena, unsafe)
    assert arena.pending_txs == []


def test_red_drill_outputs_local_tx_intents_not_direct_state_mutation():
    async def scenario():
        arena = LocalMempoolArena()
        drill = ExecutableOracleDivergenceDrill()
        context = await drill.prepare(arena, mock_target(True))
        pre = arena.get_state()
        intents = await drill.arm(arena, context)
        assert intents
        assert all(isinstance(intent, LocalTxIntent) for intent in intents)
        assert arena.get_state() == pre

    asyncio.run(scenario())


def test_blue_defense_uses_arena_mediated_intent():
    arena = MockArena()
    arena.bind_target(mock_target(True))
    action = DefenseAction(
        "pause",
        LocalTxIntent("mock://circuit-breaker", "defense_pause", "safe:defense-pause", 0, "guardian", "local", "mock-only"),
        "arena mediated defense",
    )
    execute_defense(arena, action)
    assert len(arena.pending_txs) == 1
    assert isinstance(arena.pending_txs[0], LocalTxIntent)
