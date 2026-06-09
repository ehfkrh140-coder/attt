from __future__ import annotations

import asyncio

import pytest

from arenas.evm_fork_arena import EvmForkArena
from arenas.mock_arena import MockArena
from arenas.sui_localnet_arena import SuiLocalnetArena
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from targets.target_schema import TargetProtocolSpec, mock_target


def test_evm_fork_arena_marked_unsupported_until_real_adapter():
    arena = EvmForkArena()
    assert arena.adapter_ready is False
    target = TargetProtocolSpec("MockLendingVault", "evm", "local-fork", None, "manifest", in_scope_contracts=[{"address": "mock://vault"}], authorized_scope=True, scope_confirmed=True)
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        asyncio.run(ExecutableOracleDivergenceDrill().precheck(arena, target))


def test_sui_localnet_arena_marked_unsupported_until_real_adapter():
    arena = SuiLocalnetArena()
    assert arena.adapter_ready is False
    target = TargetProtocolSpec("MockLendingVault", "sui_move", "sui-localnet", None, "manifest", in_scope_contracts=[{"address": "mock://vault"}], authorized_scope=True, scope_confirmed=True)
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        asyncio.run(ExecutableOracleDivergenceDrill().precheck(arena, target))


def test_mock_arena_is_supported_executable_arena():
    arena = MockArena()
    assert arena.adapter_ready is True
    assert asyncio.run(ExecutableOracleDivergenceDrill().precheck(arena, mock_target(True))).allowed
