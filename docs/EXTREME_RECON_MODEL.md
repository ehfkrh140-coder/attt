# Extreme Recon Model

Extreme Recon exists to make sealed-lab Red Team strong enough to stress Blue defenses honestly.

## Required model concepts

- `ReconCapabilityBoundary`
- `ReconFinding`
- `VulnerabilityClass`
- `LocalProbePlan`
- `LocalDrillCandidate`
- `BlueObservableCandidate`
- `EvaluatorInvariantCandidate`
- `ExternalWorldGap`
- `ReconEvidenceRequirement`
- `ExtremeReconScore`
- `NoFakeScenarioScore`

## Required analyzer roles

- `SurfaceMapper`
- `CanonicalIdentityAnalyzer`
- `AssetFlowGraphBuilder`
- `PermissionAuthorityGraphAnalyzer`
- `DependencyStalenessAnalyzer`
- `InvariantMiner`
- `ExploitabilityHypothesisBuilder`
- `LocalProbePlanner`
- `RedDrillSynthesizer`
- `BlueControlGenerator`
- `EvidenceRequirementBuilder`
- `ReconQualityScorer`

## Quality scoring dimensions

- `SurfaceCoverageScore`
- `DependencyCoverageScore`
- `IdentityBindingScore`
- `InvariantDiscoveryScore`
- `ExploitabilityHypothesisScore`
- `LocalExecutabilityReadinessScore`
- `BlueControlUsefulnessScore`
- `EvidenceQualityScore`
- `NoFakeScenarioScore`
- `SafetyContainmentScore`

## No narrative-only findings

A finding must include an affected surface, invariant at risk, local-only probe/drill path, expected state transition, Blue blind observable, Evaluator diff check, evidence requirement, and containment proof.
