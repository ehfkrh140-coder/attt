from __future__ import annotations

from core.invariants import InvariantSpec, check_invariant


def check_all(invariants: list[InvariantSpec], state: dict[str, object]) -> list[str]:
    return [spec.invariant_id for spec in invariants if not check_invariant(spec, state)]
