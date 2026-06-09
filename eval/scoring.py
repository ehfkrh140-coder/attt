from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from arenas.base_arena import OrderingMode


@dataclass(frozen=True)
class EvaluationResult:
    run_id: str
    target_protocol: str
    fork_block: int | None
    recon_score: float
    red_score: float
    blue_score: float
    safety_score: float
    executable_drill_count: int
    unsupported_drill_count: int
    red_impact_successes: int
    blue_blocks: int
    blue_misses: int
    false_positives: int
    false_negatives: int
    action_correctness: float
    invariant_failures: list[str]
    label_leakage_detected: bool
    public_network_blocked: bool
    extreme_drill_coverage: float
    notes: list[str] = field(default_factory=list)
    ordering_mode: OrderingMode = "defense_first"
    execution_order: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class MultiModeEvaluationResult:
    run_id: str
    target_protocol: str
    ordering_results: dict[OrderingMode, EvaluationResult]
    blue_blocks_by_mode: dict[OrderingMode, int]
    red_impact_successes_by_mode: dict[OrderingMode, int]
    action_correctness_by_mode: dict[OrderingMode, float]
    impact_by_mode: dict[OrderingMode, list[str]]
    ordering_robustness_score: float
    modes_passed: list[OrderingMode]
    modes_failed: list[OrderingMode]
