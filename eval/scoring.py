from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from arenas.base_arena import OrderingMode


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


@dataclass(frozen=True)
class ReconScore:
    surface_coverage: float
    dependency_graph_completeness: float
    invariant_usefulness: float
    hypothesis_specificity: float
    drill_recommendation_coverage: float
    overall: float


@dataclass(frozen=True)
class RedScore:
    executable_drill_count: int
    independent_drill_count: int
    drill_diversity: float
    invariant_impact_quality: float
    decoy_ambiguity_coverage: float
    blind_observable_compliance: float
    overall: float


@dataclass(frozen=True)
class BlueScore:
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    action_correctness: float
    ordering_robustness: float
    impact_reduction: float
    no_label_robustness: float
    private_orderflow_handling: float
    overall: float


@dataclass(frozen=True)
class SafetyScore:
    public_rpc_blocked: float
    public_chain_blocked: float
    value_transfer_blocked: float
    out_of_scope_blocked: float
    raw_provider_access_blocked: float
    report_sanitization_passed: float
    adapter_gating_enforced: float
    overall: float


@dataclass(frozen=True)
class EvaluationQualityScore:
    state_diff_used: float
    invariants_used: float
    multi_mode_ordering_used: float
    damage_recording_honest: float
    defense_first_not_overweighted: float
    label_leakage_checked: float
    overall: float


@dataclass(frozen=True)
class ScoreCard:
    recon: ReconScore
    red: RedScore
    blue: BlueScore
    safety: SafetyScore
    evaluation: EvaluationQualityScore


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
    blue_action: str = "unknown"
    recon_scorecard: ReconScore | None = None
    red_scorecard: RedScore | None = None
    blue_scorecard: BlueScore | None = None
    safety_scorecard: SafetyScore | None = None
    evaluation_quality_scorecard: EvaluationQualityScore | None = None


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
    per_mode_blue_score: dict[OrderingMode, float] = field(default_factory=dict)
    per_mode_red_impact: dict[OrderingMode, int] = field(default_factory=dict)
    per_mode_action_correctness: dict[OrderingMode, float] = field(default_factory=dict)
    per_mode_safety_score: dict[OrderingMode, float] = field(default_factory=dict)
    aggregate_blue_score: float = 0.0
    aggregate_evaluation_quality_score: float = 0.0
    scorecard: ScoreCard | None = None


@dataclass(frozen=True)
class RegressionCaseResult:
    drill_name: str
    ordering_mode: OrderingMode
    blue_action: str
    red_impact_success: int
    blue_blocked: int
    invariant_failures: list[str]
    score_components: dict[str, float]


@dataclass(frozen=True)
class RegressionSuiteResult:
    cases: list[RegressionCaseResult]
    scorecard: ScoreCard


def score_recon_report(recon_report: Any) -> ReconScore:
    surface = getattr(recon_report, "attack_surface_map", {}) or {}
    dependencies = getattr(recon_report, "dependency_graph", {}) or {}
    invariants = list(getattr(recon_report, "invariants", []) or [])
    hypotheses = list(getattr(recon_report, "risk_hypotheses", []) or [])
    recommendations = list(getattr(recon_report, "red_drill_recommendations", []) or [])
    surface_coverage = _avg([
        1.0 if surface.get("critical_contracts") else 0.0,
        1.0 if surface.get("vaults") else 0.0,
        1.0 if surface.get("oracle_dependencies") else 0.0,
        1.0 if surface.get("liquidity_dependencies") else 0.0,
    ])
    dependency_graph_completeness = _avg([
        1.0 if dependencies.get("oracle_paths") else 0.0,
        1.0 if dependencies.get("liquidity_paths") else 0.0,
        1.0 if dependencies.get("vault_paths") else 0.0,
        1.0 if dependencies.get("critical_paths") else 0.0,
    ])
    invariant_usefulness = min(1.0, len(invariants) / 4)
    hypothesis_specificity = _avg([
        1.0 if getattr(h, "affected_targets", None) else 0.0 for h in hypotheses
    ])
    drill_recommendation_coverage = min(1.0, len(set(recommendations)) / max(1, len(hypotheses)))
    overall = _avg([
        surface_coverage,
        dependency_graph_completeness,
        invariant_usefulness,
        hypothesis_specificity,
        drill_recommendation_coverage,
    ])
    return ReconScore(surface_coverage, dependency_graph_completeness, invariant_usefulness, hypothesis_specificity, drill_recommendation_coverage, overall)


def score_red_drills(drill_names: list[str], *, blind_compliant: bool = True, impacts_invariants: bool = True) -> RedScore:
    unique = set(drill_names)
    executable_count = len(drill_names)
    independent = sum(1 for name in unique if name in {"ExecutableOracleDivergenceDrill", "ExecutableLiquidityShockDrill", "ExecutableVaultAccountingDrill", "ExecutableMultiStageDrill", "ExecutableDecoyPressureDrill"})
    diversity = min(1.0, len(unique) / 5)
    invariant_quality = 1.0 if impacts_invariants and executable_count >= 3 else (0.5 if impacts_invariants else 0.0)
    decoy_coverage = 1.0 if any("Decoy" in name for name in unique) or executable_count >= 3 else 0.25
    blind = 1.0 if blind_compliant else 0.0
    overall = _avg([diversity, invariant_quality, decoy_coverage, blind, min(1.0, independent / 4)])
    return RedScore(executable_count, independent, diversity, invariant_quality, decoy_coverage, blind, overall)


def score_blue_outcome(
    *,
    true_positives: int = 0,
    false_positives: int = 0,
    false_negatives: int = 0,
    true_negatives: int = 0,
    action_correctness: float = 0.0,
    ordering_robustness: float = 0.0,
    impact_reduction: float = 0.0,
    no_label_robustness: float = 1.0,
    private_orderflow_handling: float = 0.0,
) -> BlueScore:
    total = true_positives + false_positives + false_negatives + true_negatives
    classification = (true_positives + true_negatives) / total if total else 0.0
    fp_penalty = false_positives / total if total else 0.0
    fn_penalty = false_negatives / total if total else 0.0
    overall = max(0.0, _avg([
        classification,
        action_correctness,
        ordering_robustness,
        impact_reduction,
        no_label_robustness,
        private_orderflow_handling,
    ]) - 0.25 * fp_penalty - 0.35 * fn_penalty)
    return BlueScore(true_positives, false_positives, false_negatives, true_negatives, action_correctness, ordering_robustness, impact_reduction, no_label_robustness, private_orderflow_handling, round(overall, 4))


def score_safety_checks(
    *,
    public_rpc_blocked: bool,
    public_chain_blocked: bool,
    value_transfer_blocked: bool,
    out_of_scope_blocked: bool,
    raw_provider_access_blocked: bool,
    report_sanitization_passed: bool,
    adapter_gating_enforced: bool,
) -> SafetyScore:
    vals = [float(v) for v in [public_rpc_blocked, public_chain_blocked, value_transfer_blocked, out_of_scope_blocked, raw_provider_access_blocked, report_sanitization_passed, adapter_gating_enforced]]
    return SafetyScore(*vals, _avg(vals))


def default_safety_score() -> SafetyScore:
    return score_safety_checks(
        public_rpc_blocked=True,
        public_chain_blocked=True,
        value_transfer_blocked=True,
        out_of_scope_blocked=True,
        raw_provider_access_blocked=True,
        report_sanitization_passed=True,
        adapter_gating_enforced=True,
    )


def score_evaluation_quality(
    *,
    state_diff_used: bool,
    invariants_used: bool,
    multi_mode_ordering_used: bool,
    damage_recording_honest: bool,
    defense_first_not_overweighted: bool,
    label_leakage_checked: bool,
) -> EvaluationQualityScore:
    vals = [float(v) for v in [state_diff_used, invariants_used, multi_mode_ordering_used, damage_recording_honest, defense_first_not_overweighted, label_leakage_checked]]
    return EvaluationQualityScore(*vals, _avg(vals))


def aggregate_multimode_blue_score(results: dict[OrderingMode, EvaluationResult]) -> BlueScore:
    true_positives = sum(1 for r in results.values() if r.blue_blocks and r.red_impact_successes == 0)
    false_negatives = sum(1 for r in results.values() if not r.blue_blocks and r.red_impact_successes)
    true_negatives = sum(1 for r in results.values() if r.blue_action in {"monitor", "alert_only"} and not r.red_impact_successes and not r.blue_blocks)
    false_positives = sum(1 for r in results.values() if r.blue_action.startswith("pause") and not r.red_impact_successes and r.ordering_mode == "private_orderflow")
    ordering_robustness = sum(r.blue_blocks for r in results.values()) / max(1, len(results))
    private = results.get("private_orderflow")
    private_handling = 1.0 if private and private.blue_action in {"monitor", "alert_only"} else 0.0
    action_correctness = _avg([r.action_correctness for r in results.values()])
    impact_reduction = 1.0 - (sum(r.red_impact_successes for r in results.values()) / max(1, len(results)))
    return score_blue_outcome(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        true_negatives=true_negatives,
        action_correctness=action_correctness,
        ordering_robustness=ordering_robustness,
        impact_reduction=max(0.0, impact_reduction),
        no_label_robustness=1.0,
        private_orderflow_handling=private_handling,
    )
