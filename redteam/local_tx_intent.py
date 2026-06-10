from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocalTxIntent:
    target: str
    function_category: str
    calldata_label: str
    value: int
    sender_role: str
    gas_strategy: str
    safety_scope: str

    def public_report_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "function_category": self.function_category,
            "calldata_label": self.calldata_label,
            "value": self.value,
            "sender_role": self.sender_role,
            "gas_strategy": self.gas_strategy,
            "safety_scope": self.safety_scope,
        }
