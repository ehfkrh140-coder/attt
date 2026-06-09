from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from core.errors import SafetyGuardError
from redteam.local_tx_intent import LocalTxIntent
from targets.target_schema import TargetProtocolSpec

BLOCKED_BY_SAFETY_GUARD = "BLOCKED_BY_SAFETY_GUARD"
# Explicit local test chain IDs only. Chain ID 0 is intentionally not allowed.
LOCAL_EVM_CHAIN_IDS = {31337, 1337}
LOCAL_SUI_CHAIN_IDS = {900}
DOCUMENTED_LOCAL_TEST_CHAIN_IDS = {999}
LOCAL_CHAIN_IDS = LOCAL_EVM_CHAIN_IDS | LOCAL_SUI_CHAIN_IDS | DOCUMENTED_LOCAL_TEST_CHAIN_IDS
PUBLIC_CHAIN_IDS = {1, 10, 56, 100, 137, 250, 42161, 43114, 8453}

_REPORT_FORBIDDEN_SUBSTRINGS = (
    "raw_calldata",
    "calldata:",
    "private_key",
    "mnemonic",
    "seed phrase",
    "send_raw_transaction",
    "eth_sendrawtransaction",
    "sign_transaction",
    "account.sign_transaction",
    "exploit code",
    "reusable transaction payload",
    "infura",
    "alchemy",
    "quicknode",
    "ankr",
    "blastapi",
    "publicnode",
)
_LONG_HEX_RE = re.compile(r"0x[a-fA-F0-9]{16,}")
_PUBLIC_RPC_URL_RE = re.compile(r"https?://(?!localhost(?::|/|$)|127\.0\.0\.1(?::|/|$)|\[::1\](?::|/|$))", re.IGNORECASE)
_CURL_RPC_POST_RE = re.compile(r"curl\b[^\n]*(?:-X\s*POST|-d\b|--data)", re.IGNORECASE)


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
        if chain_id in PUBLIC_CHAIN_IDS or chain_id == 0:
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        if chain_id in self.allowed_chain_ids:
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_scope_confirmed(self, target: TargetProtocolSpec | None) -> SafetyDecision:
        if target is not None and target.is_executable_scope():
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_target_in_scope(self, tx: LocalTxIntent, target: TargetProtocolSpec | None) -> SafetyDecision:
        self.assert_scope_confirmed(target)
        assert target is not None
        if tx.target.lower() in target.in_scope_addresses:
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_zero_value(self, tx: LocalTxIntent) -> SafetyDecision:
        if tx.value == 0:
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_arena_local(self, arena: object) -> SafetyDecision:
        if not getattr(arena, "is_local", False):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        self.assert_local_rpc(getattr(arena, "rpc_url", ""))
        self.assert_local_chain(int(getattr(arena, "chain_id", -1)))
        return SafetyDecision(True)

    def assert_adapter_ready(self, arena: object) -> SafetyDecision:
        if not getattr(arena, "adapter_ready", False):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        return SafetyDecision(True)

    def assert_arena_mediated_intent(self, tx: LocalTxIntent) -> SafetyDecision:
        if isinstance(tx, LocalTxIntent):
            return SafetyDecision(True)
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def assert_tx_allowed(self, tx: LocalTxIntent, arena: object, target: TargetProtocolSpec | None) -> SafetyDecision:
        self.assert_arena_mediated_intent(tx)
        self.assert_arena_local(arena)
        self.assert_adapter_ready(arena)
        self.assert_scope_confirmed(target)
        self.assert_target_in_scope(tx, target)
        self.assert_zero_value(tx)
        return SafetyDecision(True)

    def assert_drill_allowed(self, drill: object, arena: object, target: TargetProtocolSpec) -> SafetyDecision:
        self.assert_arena_local(arena)
        self.assert_adapter_ready(arena)
        self.assert_scope_confirmed(target)
        runtime = getattr(arena, "runtime", None)
        if getattr(drill, "required_runtime", None) != runtime:
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        return SafetyDecision(True)

    def assert_safe_report(self, report: str) -> SafetyDecision:
        lowered = report.lower()
        if any(token in lowered for token in _REPORT_FORBIDDEN_SUBSTRINGS):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        if _LONG_HEX_RE.search(report):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        if _PUBLIC_RPC_URL_RE.search(report):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        if _CURL_RPC_POST_RE.search(report):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        return SafetyDecision(True)
