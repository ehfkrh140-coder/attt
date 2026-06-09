from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InvariantSpec:
    invariant_id: str
    target: str
    risk_type: str
    description: str
    preconditions: list[str]
    check_method: str
    failure_condition: str
    severity_if_failed: str


def check_invariant(spec: InvariantSpec, state: dict[str, Any]) -> bool:
    if spec.check_method == "oracle_deviation_within_threshold":
        oracle = float(state["oracle_price"])
        pool = float(state["pool_price"])
        threshold = float(state.get("max_oracle_deviation", 0.10))
        return abs(oracle - pool) / max(pool, 1.0) <= threshold or bool(state.get("paused"))
    if spec.check_method == "vault_accounting_consistent":
        assets = float(state["vault_assets"])
        liabilities = float(state["vault_liabilities"])
        return assets + 1e-9 >= liabilities or bool(state.get("paused"))
    if spec.check_method == "liquidity_above_floor":
        return float(state["pool_liquidity"]) >= float(state.get("min_pool_liquidity", 100.0)) or bool(state.get("paused"))
    return True
