from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

AAVE_MAX_RESERVES_DEFAULT = 8
AAVE_MAX_RESERVES_HARD_CAP = 50


@dataclass(frozen=True)
class AaveV3CoreContracts:
    pool_addresses_provider: str
    pool: str | None = None
    pool_configurator: str | None = None
    price_oracle: str | None = None
    acl_manager: str | None = None
    pool_admin_role: str | None = None
    risk_admin_role: str | None = None

    def safe_dict(self) -> dict[str, Any]:
        return {
            "pool_addresses_provider": self.pool_addresses_provider,
            "pool": self.pool,
            "pool_configurator": self.pool_configurator,
            "price_oracle": self.price_oracle,
            "acl_manager": self.acl_manager,
            "pool_admin_role": self.pool_admin_role,
            "risk_admin_role": self.risk_admin_role,
        }


@dataclass(frozen=True)
class AaveV3ReserveSnapshot:
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
    asset_price: int | None = None
    oracle_source: str | None = None
    discovery_status: str = "partial"
    unresolved_fields: list[str] = field(default_factory=list)
    watch_items: list[str] = field(default_factory=list)
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
            ("oracle_source", self.oracle_source, "reserve_oracle_source"),
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
            "asset_price_status": "available" if self.asset_price is not None else "unavailable",
            "oracle_source_status": "available" if self.oracle_source else "unavailable",
            "discovery_status": self.discovery_status,
            "unresolved_fields": list(self.unresolved_fields),
            "watch_items": list(self.watch_items),
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
                    "oracle_source": self.oracle_source,
                }
            )
        return data


class AaveReserveMetadata(AaveV3ReserveSnapshot):
    """Backward-compatible name for reserve snapshots."""


@dataclass(frozen=True)
class AaveV3ReadOnlyDiscoveryReport:
    core_contracts: AaveV3CoreContracts
    reserves: list[AaveV3ReserveSnapshot] = field(default_factory=list)
    reserve_discovery_status: str = "unavailable"
    max_reserves_requested: int = AAVE_MAX_RESERVES_DEFAULT
    max_reserves_processed: int = AAVE_MAX_RESERVES_DEFAULT
    hard_cap_applied: bool = False
    truncated: bool = False
    unresolved_calls: list[str] = field(default_factory=list)
    unresolved_reserve_fields: list[str] = field(default_factory=list)
    watch_items: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def reserve_cap(self) -> int:
        return self.max_reserves_processed

    def safe_dict(self) -> dict[str, Any]:
        return {
            "core_contracts": self.core_contracts.safe_dict(),
            "reserve_discovery_status": self.reserve_discovery_status,
            "reserve_count": len(self.reserves),
            "max_reserves_requested": self.max_reserves_requested,
            "max_reserves_processed": self.max_reserves_processed,
            "reserve_cap": self.max_reserves_processed,
            "hard_cap_applied": self.hard_cap_applied,
            "truncated": self.truncated,
            "unresolved_calls": list(self.unresolved_calls),
            "unresolved_reserve_fields": list(self.unresolved_reserve_fields),
            "watch_items": list(self.watch_items),
            "warnings": list(self.warnings),
            "reserves": [reserve.safe_dict() for reserve in self.reserves],
        }


class AaveV3ReadOnlyMetadata(AaveV3ReadOnlyDiscoveryReport):
    """Backward-compatible metadata class name."""
