from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard

READONLY_RPC_METHODS = {
    "eth_chainId",
    "eth_getCode",
    "eth_call",
    "eth_getStorageAt",
    "eth_getBalance",
    "net_version",
    "web3_clientVersion",
}
FORBIDDEN_RPC_PREFIXES = ("wallet_", "personal_", "debug_", "txpool_", "anvil_set", "hardhat_set", "evm_set")
FORBIDDEN_RPC_METHODS = {
    "eth_sendTransaction",
    "eth_sendRawTransaction",
    "personal_sign",
    "eth_sign",
    "eth_signTransaction",
}


class EvmJsonRpcError(RuntimeError):
    """Safe read-only RPC error without raw payload details."""


@dataclass(frozen=True)
class RpcResult:
    method: str
    result: Any


Requester = Callable[[str, dict[str, Any], float], dict[str, Any]]


class EvmJsonRpcTransport:
    def __init__(self, local_rpc_url: str, timeout_seconds: float = 5.0, requester: Requester | None = None) -> None:
        SafetyGuard().assert_local_rpc(local_rpc_url)
        self.local_rpc_url = local_rpc_url
        self.timeout_seconds = timeout_seconds
        self._requester = requester or self._default_requester

    def call(self, method: str, params: list[object] | None = None) -> object:
        self._assert_allowed_method(method)
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params or [])}
        try:
            response = self._requester(self.local_rpc_url, payload, self.timeout_seconds)
        except (OSError, TimeoutError, urllib.error.URLError) as exc:
            raise EvmJsonRpcError("LOCAL_FORK_UNAVAILABLE") from exc
        if "error" in response:
            raise EvmJsonRpcError("LOCAL_FORK_UNAVAILABLE")
        return RpcResult(method=method, result=response.get("result")).result

    def _assert_allowed_method(self, method: str) -> None:
        if method in FORBIDDEN_RPC_METHODS or any(method.startswith(prefix) for prefix in FORBIDDEN_RPC_PREFIXES):
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
        if method not in READONLY_RPC_METHODS:
            raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)

    def _default_requester(self, url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL is SafetyGuard-localhost checked.
            return json.loads(response.read().decode("utf-8"))
