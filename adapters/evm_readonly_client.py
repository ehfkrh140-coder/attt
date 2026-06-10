from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.safety import SafetyGuard


@dataclass
class EvmReadonlyClient:
    local_rpc_url: str = "http://127.0.0.1:8545"
    chain_id: int = 31337
    code_by_address: dict[str, str] = field(default_factory=dict)
    storage: dict[tuple[str, str], str] = field(default_factory=dict)
    balances: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        guard = SafetyGuard()
        guard.assert_local_rpc(self.local_rpc_url)
        guard.assert_local_chain(self.chain_id)

    def get_code(self, address: str) -> str:
        return self.code_by_address.get(address.lower(), "0x")

    def eth_call(self, target: str, data_label: str) -> dict[str, Any]:
        return {"target": target, "data_label": data_label, "mode": "readonly_local_fork"}

    def get_storage_at(self, address: str, slot: str) -> str:
        return self.storage.get((address.lower(), slot), "0x0")

    def get_balance(self, address: str) -> int:
        return self.balances.get(address.lower(), 0)
