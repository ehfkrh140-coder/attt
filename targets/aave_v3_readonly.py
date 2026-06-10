from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AaveReserveMetadata:
    """Read-only reserve metadata discovered from an Aave V3 Pool."""

    asset: str
    symbol: str = "unknown"
    a_token: str | None = None
    stable_debt_token: str | None = None
    variable_debt_token: str | None = None
    interest_rate_strategy: str | None = None
    decimals: int | None = None
    ltv_bps: int | None = None
    liquidation_threshold_bps: int | None = None
    borrowing_enabled: bool | None = None
    stable_borrow_enabled: bool | None = None
    active: bool | None = None
    frozen: bool | None = None
    discovery_status: str = "partial"
    notes: list[str] = field(default_factory=list)

    def safe_name(self, index: int) -> str:
        suffix = self.symbol if self.symbol and self.symbol != "unknown" else f"reserve_{index}"
        return f"AaveV3Reserve_{suffix}"

    def token_contracts(self, index: int) -> list[dict[str, Any]]:
        reserve_name = self.safe_name(index)
        contracts: list[dict[str, Any]] = [
            {
                "name": reserve_name,
                "address": self.asset,
                "category": "reserve_asset",
                "metadata": self.safe_dict(include_addresses=False),
            }
        ]
        token_fields = [
            ("a_token", self.a_token, "a_token"),
            ("stable_debt_token", self.stable_debt_token, "stable_debt_token"),
            ("variable_debt_token", self.variable_debt_token, "variable_debt_token"),
        ]
        for label, address, category in token_fields:
            if address:
                contracts.append(
                    {
                        "name": f"{reserve_name}_{label}",
                        "address": address,
                        "category": category,
                        "dependencies": [self.asset],
                    }
                )
        return contracts

    def safe_dict(self, *, include_addresses: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "symbol": self.symbol,
            "decimals": self.decimals,
            "ltv_bps": self.ltv_bps,
            "liquidation_threshold_bps": self.liquidation_threshold_bps,
            "borrowing_enabled": self.borrowing_enabled,
            "stable_borrow_enabled": self.stable_borrow_enabled,
            "active": self.active,
            "frozen": self.frozen,
            "discovery_status": self.discovery_status,
            "notes": list(self.notes),
        }
        if include_addresses:
            data.update(
                {
                    "asset": self.asset,
                    "a_token": self.a_token,
                    "stable_debt_token": self.stable_debt_token,
                    "variable_debt_token": self.variable_debt_token,
                    "interest_rate_strategy": self.interest_rate_strategy,
                }
            )
        return data


@dataclass(frozen=True)
class AaveV3ReadOnlyMetadata:
    reserves: list[AaveReserveMetadata] = field(default_factory=list)
    reserve_discovery_status: str = "unavailable"
    reserve_cap: int = 20
    notes: list[str] = field(default_factory=list)

    def safe_dict(self) -> dict[str, Any]:
        return {
            "reserve_discovery_status": self.reserve_discovery_status,
            "reserve_count": len(self.reserves),
            "reserve_cap": self.reserve_cap,
            "reserves": [reserve.safe_dict() for reserve in self.reserves],
            "notes": list(self.notes),
        }
