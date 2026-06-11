# Recon to Red Drill Pipeline — Phase 2A.5-R

## Required flow

```text
TargetProtocolSpec
→ ReconFinding
→ LocalProbePlan / LocalDrillCandidate
→ BlueObservableCandidate
→ EvaluatorInvariantCandidate
→ ReconEvidenceRequirement
→ Safety containment review
→ MockArena drill now or Phase 2B sealed-local drill later
```

## ReconFinding minimum fields

- affected surface
- invariant at risk
- local-only probe plan or drill candidate
- Blue blind observable candidate
- Evaluator invariant candidate
- evidence requirement
- safety containment requirement

## Red drill candidate requirements

A Red drill candidate must be non-portable, local-only, manifest-scoped, invariant-targeted, and evidence-producing. It must not contain public-network procedure, raw reusable calldata, transaction bundles, or copy-paste attack scripts.

## Blue observable requirements

Blue receives blind operational features: target category, call shape, sender profile, timing pattern, dependency context, state delta hints, vault/reserve/accounting deltas, identity mismatch indicators, visibility mode, and ordering hints.

Blue must not receive Red drill name, exploit label, exact Red path, Red success condition, or privileged evaluator answer.

## Evaluator requirements

Evaluator must receive state-diff or invariant-diff checks. Labels alone are insufficient.
