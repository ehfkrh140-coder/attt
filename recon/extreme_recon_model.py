from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VulnerabilityClass(str, Enum):
    CANONICAL_ASSET_IDENTITY_FAILURE = "CanonicalAssetIdentityFailure"
    DEPENDENCY_STALENESS = "DependencyStaleness"
    RESIDUAL_ASSET_SURFACE = "ResidualAssetSurface"
    PERMISSION_AUTHORITY_BOUNDARY = "PermissionAuthorityBoundary"
    ORACLE_KEEPER_DEPENDENCY_GAP = "OracleKeeperDependencyGap"
    ACCOUNTING_INVARIANT_PRESSURE = "AccountingInvariantPressure"


@dataclass(frozen=True)
class LocalProbePlan:
    name: str
    local_only: bool
    manifest_scoped: bool
    expected_state_transition: str
    safety_containment: str

    def is_sufficient(self) -> bool:
        return bool(self.name and self.local_only and self.manifest_scoped and self.expected_state_transition and self.safety_containment)


@dataclass(frozen=True)
class LocalDrillCandidate:
    name: str
    local_only: bool
    invariant_pressure: str
    expected_state_diff: str
    sanitized_trace_required: bool = True
    non_portable: bool = True

    def is_sufficient(self) -> bool:
        return all((self.name, self.local_only, self.invariant_pressure, self.expected_state_diff, self.sanitized_trace_required, self.non_portable))


@dataclass(frozen=True)
class BlueObservableCandidate:
    observable_type: str
    blind_feature: str
    leaks_red_label: bool = False

    def is_blind(self) -> bool:
        forbidden = ("exploit", "drill_name", "red_path", "success_condition")
        lowered = f"{self.observable_type} {self.blind_feature}".lower()
        return not self.leaks_red_label and not any(token in lowered for token in forbidden)


@dataclass(frozen=True)
class EvaluatorInvariantCandidate:
    invariant_name: str
    state_diff_check: str | None = None
    invariant_diff_check: str | None = None

    def has_diff_evidence(self) -> bool:
        return bool(self.state_diff_check or self.invariant_diff_check)


@dataclass(frozen=True)
class ExternalWorldGap:
    dependency: str
    missing_twin_pressure: str
    local_model_requirement: str


@dataclass(frozen=True)
class ReconEvidenceRequirement:
    evidence_type: str
    required_artifact: str
    sanitized: bool = True
    no_replayable_payload: bool = True

    def is_sufficient(self) -> bool:
        return bool(self.evidence_type and self.required_artifact and self.sanitized and self.no_replayable_payload)


@dataclass(frozen=True)
class ReconFinding:
    finding_id: str
    vulnerability_class: VulnerabilityClass
    affected_surface: str
    invariant_at_risk: str | None = None
    local_probe_plan: LocalProbePlan | None = None
    local_drill_candidate: LocalDrillCandidate | None = None
    blue_observable_candidate: BlueObservableCandidate | None = None
    evaluator_invariant_candidate: EvaluatorInvariantCandidate | None = None
    evidence_requirement: ReconEvidenceRequirement | None = None
    safety_containment_requirement: str | None = None
    narrative_only: bool = False

    def is_sufficient(self) -> bool:
        return all(
            (
                not self.narrative_only,
                bool(self.affected_surface),
                bool(self.invariant_at_risk),
                bool(self.local_probe_plan and self.local_probe_plan.is_sufficient() or self.local_drill_candidate and self.local_drill_candidate.is_sufficient()),
                bool(self.blue_observable_candidate and self.blue_observable_candidate.is_blind()),
                bool(self.evaluator_invariant_candidate and self.evaluator_invariant_candidate.has_diff_evidence()),
                bool(self.evidence_requirement and self.evidence_requirement.is_sufficient()),
                bool(self.safety_containment_requirement),
            )
        )


@dataclass(frozen=True)
class ExtremeReconScore:
    surface_coverage: float
    dependency_coverage: float
    identity_binding: float
    invariant_discovery: float
    exploitability_hypothesis: float
    local_executability_readiness: float
    blue_control_usefulness: float
    evidence_quality: float
    no_fake_scenario: float
    safety_containment: float

    def overall(self) -> float:
        values = (
            self.surface_coverage,
            self.dependency_coverage,
            self.identity_binding,
            self.invariant_discovery,
            self.exploitability_hypothesis,
            self.local_executability_readiness,
            self.blue_control_usefulness,
            self.evidence_quality,
            self.no_fake_scenario,
            self.safety_containment,
        )
        if any(value < 0 or value > 1 for value in values):
            raise ValueError("score_out_of_range")
        return sum(values) / len(values)


class SurfaceMapper: ...
class CanonicalIdentityAnalyzer: ...
class AssetFlowGraphBuilder: ...
class PermissionAuthorityGraphAnalyzer: ...
class DependencyStalenessAnalyzer: ...
class InvariantMiner: ...
class ExploitabilityHypothesisBuilder: ...
class LocalProbePlanner: ...
class RedDrillSynthesizer: ...
class BlueControlGenerator: ...
class EvidenceRequirementBuilder: ...


class ReconQualityScorer:
    def score_findings(self, findings: tuple[ReconFinding, ...]) -> ExtremeReconScore:
        if not findings:
            return ExtremeReconScore(0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
        sufficient_ratio = sum(1 for finding in findings if finding.is_sufficient()) / len(findings)
        return ExtremeReconScore(
            surface_coverage=sufficient_ratio,
            dependency_coverage=sufficient_ratio,
            identity_binding=sufficient_ratio,
            invariant_discovery=sufficient_ratio,
            exploitability_hypothesis=sufficient_ratio,
            local_executability_readiness=sufficient_ratio,
            blue_control_usefulness=sufficient_ratio,
            evidence_quality=sufficient_ratio,
            no_fake_scenario=sufficient_ratio,
            safety_containment=1.0,
        )
