from __future__ import annotations

from dataclasses import dataclass, field


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
