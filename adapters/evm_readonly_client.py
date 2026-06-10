from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adapters.evm_call_builder import EvmCall, EvmCallBuilder
from adapters.evm_json_rpc_transport import EvmJsonRpcTransport
from core.safety import SafetyGuard

LOCAL_FORK_UNAVAILABLE = "LOCAL_FORK_UNAVAILABLE"


def _hex_to_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16) if value.startswith("0x") else int(value)
    return 0


@dataclass
class EvmReadonlyClient:
    local_rpc_url: str = "http://127.0.0.1:8545"
    chain_id: int = 31337
    code_by_address: dict[str, str] = field(default_factory=dict)
    storage: dict[tuple[str, str], str] = field(default_factory=dict)
    balances: dict[str, int] = field(default_factory=dict)
    call_results: dict[tuple[Any, ...] | str, Any] = field(default_factory=dict)
    fork_block: str | int | None = None
    transport: EvmJsonRpcTransport | None = None

    def __post_init__(self) -> None:
        guard = SafetyGuard()
        guard.assert_local_rpc(self.local_rpc_url)
        guard.assert_local_chain(self.chain_id)

    def get_chain_id(self) -> int:
        if self.transport is None:
            return self.chain_id
        chain_id = _hex_to_int(self.transport.call("eth_chainId", []))
        SafetyGuard().assert_local_chain(chain_id)
        self.chain_id = chain_id
        return chain_id

    def get_code(self, address: str) -> str:
        if self.transport is not None:
            return str(self.transport.call("eth_getCode", [address, "latest"]))
        return self.code_by_address.get(address.lower(), "0x")

    def eth_call(self, to: str, call: EvmCall | str) -> Any:
        evm_call = self._coerce_call(call)
        if self.transport is not None:
            return self.transport.call("eth_call", [{"to": to, "data": evm_call.data}, "latest"])

        call_args = tuple(arg.lower() for arg in (evm_call.lookup_args or evm_call.encoded_args) if arg)
        scoped_arg_key = (to.lower(), evm_call.safe_label, *call_args)
        if scoped_arg_key in self.call_results:
            return self.call_results[scoped_arg_key]
        scoped_key = (to.lower(), evm_call.safe_label)
        if scoped_key in self.call_results:
            return self.call_results[scoped_key]
        if evm_call.safe_label in self.call_results:
            return self.call_results[evm_call.safe_label]

        # Backward compatibility for older fixture labels used before Phase 2A.1.
        legacy_label = _LEGACY_AAVE_LABELS.get(evm_call.safe_label)
        if legacy_label is not None:
            legacy_scoped_key = (to.lower(), legacy_label)
            if legacy_scoped_key in self.call_results:
                return self.call_results[legacy_scoped_key]
            if legacy_label in self.call_results:
                return self.call_results[legacy_label]
        return None

    def safe_call(self, to: str, safe_label: str) -> Any:
        return self.eth_call(to, EvmCallBuilder.build(safe_label))

    def get_storage_at(self, address: str, slot: str) -> str:
        if self.transport is not None:
            return str(self.transport.call("eth_getStorageAt", [address, slot, "latest"]))
        return self.storage.get((address.lower(), slot), "0x0")

    def get_balance(self, address: str) -> int:
        if self.transport is not None:
            return _hex_to_int(self.transport.call("eth_getBalance", [address, "latest"]))
        return self.balances.get(address.lower(), 0)

    def _coerce_call(self, call: EvmCall | str) -> EvmCall:
        if isinstance(call, EvmCall):
            return call
        return EvmCallBuilder.build(call)


_LEGACY_AAVE_LABELS = {
    "aave_provider_get_pool": "getPool()",
    "aave_provider_get_pool_configurator": "getPoolConfigurator()",
    "aave_provider_get_price_oracle": "getPriceOracle()",
    "aave_provider_get_acl_manager": "getACLManager()",
}
