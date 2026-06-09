from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from core.errors import SafetyGuardError
from redteam.local_tx_intent import LocalTxIntent
from targets.target_schema import TargetProtocolSpec

BLOCKED_BY_SAFETY_GUARD = "BLOCKED_BY_SAFETY_GUARD"
LOCAL_CHAIN_IDS = {31337, 1337, 900, 999, 0}


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str = "OK"


class SafetyGuard:
    def __init__(self, allowed_chain_ids: set[int] | None = None) -> None:
        self.allowed_chain_ids = allowed_chain_ids or LOCAL_CHAIN_IDS

    def assert_local_rpc(self, rpc_url: str) -> SafetyDecision:
        parsed = urlparse(rpc_url)
        host = parsed.hostname or ""
        if host in {"localhost", "127.0.0.1", "::1"} or rpc_url.startswith("mock://"):
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_local_chain(self, chain_id: int) -> SafetyDecision:
        if chain_id in self.allowed_chain_ids:
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_scope_confirmed(self, target: TargetProtocolSpec) -> SafetyDecision:
        if target.is_executable_scope():
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_target_in_scope(self, tx: LocalTxIntent, target: TargetProtocolSpec) -> SafetyDecision:
        if tx.target.lower() in target.in_scope_addresses:
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_drill_allowed(self, drill: object, arena: object, target: TargetProtocolSpec) -> SafetyDecision:
        self.assert_scope_confirmed(target)
        runtime = getattr(arena, "runtime", None)
        if getattr(drill, "required_runtime", None) != runtime:
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        if not getattr(arena, "is_local", False):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        self.assert_local_rpc(getattr(arena, "rpc_url", ""))
        self.assert_local_chain(int(getattr(arena, "chain_id", -1)))
        return SafetyDecision(True)

    def assert_safe_report(self, report: str) -> SafetyDecision:
        lowered = report.lower()
        forbidden = ["raw_calldata", "0xdeadbeef", "send_raw_transaction", "private_key"]
        if any(token in lowered for token in forbidden):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        return SafetyDecision(True)
