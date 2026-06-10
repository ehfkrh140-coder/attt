from __future__ import annotations

import shutil
from dataclasses import dataclass

from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard

MISSING_LOCAL_FORK_TOOL = "MISSING_LOCAL_FORK_TOOL"
LOCAL_FORK_UNAVAILABLE = "LOCAL_FORK_UNAVAILABLE"


@dataclass(frozen=True)
class EvmForkConfig:
    protocol: str
    network: str
    fork_block: str | int | None
    upstream_rpc_env: str | None
    local_rpc_url: str = "http://127.0.0.1:8545"
    chain_id: int = 31337


@dataclass(frozen=True)
class ForkStatus:
    available: bool
    local_rpc_url: str
    chain_id: int | None
    fork_block: str | int | None
    tool: str | None
    reason: str | None

    def safe_summary(self) -> dict[str, object]:
        return {
            "available": self.available,
            "chain_id": self.chain_id,
            "fork_block": self.fork_block,
            "tool": self.tool,
            "reason": self.reason,
        }


class EvmForkController:
    def __init__(self, safety_guard: SafetyGuard | None = None) -> None:
        self.safety_guard = safety_guard or SafetyGuard()

    def assert_safe_bot_rpc(self, config: EvmForkConfig) -> None:
        try:
            self.safety_guard.assert_local_rpc(config.local_rpc_url)
            self.safety_guard.assert_local_chain(config.chain_id)
        except SafetyGuardError as exc:
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD) from exc


    def verify_existing_local_fork(self, config: EvmForkConfig, client: object | None = None) -> ForkStatus:
        self.assert_safe_bot_rpc(config)
        if client is None:
            return ForkStatus(
                available=False,
                local_rpc_url=config.local_rpc_url,
                chain_id=config.chain_id,
                fork_block=config.fork_block,
                tool="existing-local-fork",
                reason=LOCAL_FORK_UNAVAILABLE,
            )
        chain_id = int(client.get_chain_id()) if hasattr(client, "get_chain_id") else config.chain_id
        self.safety_guard.assert_local_chain(chain_id)
        fork_block = getattr(client, "fork_block", config.fork_block)
        return ForkStatus(
            available=True,
            local_rpc_url=config.local_rpc_url,
            chain_id=chain_id,
            fork_block=fork_block,
            tool="existing-local-fork",
            reason="local_fork_readonly_available",
        )

    def verify_local_fork(self, config: EvmForkConfig) -> ForkStatus:
        self.assert_safe_bot_rpc(config)
        return ForkStatus(
            available=True,
            local_rpc_url=config.local_rpc_url,
            chain_id=config.chain_id,
            fork_block=config.fork_block,
            tool="existing-local-fork",
            reason="local_fork_rpc_is_safe_for_bot_connections",
        )

    def start_local_fork(self, config: EvmForkConfig) -> ForkStatus:
        self.assert_safe_bot_rpc(config)
        tool = "anvil" if shutil.which("anvil") else "hardhat" if shutil.which("hardhat") else None
        if tool is None:
            return ForkStatus(
                available=False,
                local_rpc_url=config.local_rpc_url,
                chain_id=config.chain_id,
                fork_block=config.fork_block,
                tool=None,
                reason=MISSING_LOCAL_FORK_TOOL,
            )
        return ForkStatus(
            available=False,
            local_rpc_url=config.local_rpc_url,
            chain_id=config.chain_id,
            fork_block=config.fork_block,
            tool=tool,
            reason="local_fork_start_is_gated_in_mvp",
        )
