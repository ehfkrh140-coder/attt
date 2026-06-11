# Phase 2A.6-Live Review — User-Provided Live-Local Artifact Assessment

## Purpose

Phase 2A.6-Live Review lets a user collect read-only artifacts from their own localhost fork workflow and
submit those files for deterministic repository-side review.

This is still a review-only phase. It does not enable Phase 2B, does not execute Red drills, does not send
transactions, and does not connect bots to public RPC.

## Core rule

External public-world behavior is forbidden. Internal sealed-lab equivalents must be modeled with maximum
realism.

외부 세계에서는 금지한다. 내부 실험실에서는 현실과 똑같이, 오히려 더 극한적으로 구현한다.

Red가 최강이려면 Recon은 더 최강이어야 한다.

For Red to be world-class, Recon must be stronger than Red.

## Supported user-provided artifacts

A live artifact bundle may include any subset of these local files:

1. `live_fork_check.md` — localhost fork reachability evidence.
2. `aave_readonly_discovery.md` — Aave V3 read-only discovery evidence.
3. `aave_v3_evidence_pack.md` or `live_fork_evidence_pack.md` — Phase 2A.5 evidence pack.
4. `aave_v3_readonly.yaml` or `target_manifest.yaml` — exported target manifest.
5. `dependency_graph_review.md` — dependency graph review.
6. `target_manifest_review.md` — target manifest review.
7. `manual_live_fork_smoke_result.md` — optional manual localhost smoke result.
8. `phase2b_preflight.md` — Phase 2B preflight review output.
9. `live_fork_evidence_quality_report.md` — optional prior Phase 2A.6 report.

Missing artifacts are accepted as review findings. Missing artifacts are not treated as execution permission.

## Localhost-only generation commands

The user may generate artifacts with existing read-only scripts. Commands that touch a fork must point only
to `localhost`, `127.0.0.1`, `::1`, or `mock://` endpoints.

Example safe patterns:

```bash
python scripts/check_local_evm_fork.py \
  --rpc-url http://127.0.0.1:8545 \
  --output artifacts/live_fork_check.md
python scripts/aave_readonly_discovery.py \
  --rpc-url http://127.0.0.1:8545 \
  --output artifacts/aave_readonly_discovery.md
python scripts/generate_live_fork_evidence_pack.py \
  --fixture-readonly \
  --output artifacts/aave_v3_evidence_pack.md
python scripts/review_target_manifest.py \
  --target-manifest artifacts/aave_v3_readonly.yaml \
  --output artifacts/target_manifest_review.md
python scripts/generate_dependency_graph_review.py \
  --target-manifest artifacts/aave_v3_readonly.yaml \
  --output artifacts/dependency_graph_review.md
python scripts/manual_live_fork_smoke.py --output artifacts/manual_live_fork_smoke_result.md
python scripts/phase2b_preflight.py \
  --target-manifest artifacts/aave_v3_readonly.yaml \
  --output artifacts/phase2b_preflight.md
```

The fixture command is CI-friendly. It is useful for deterministic review but cannot approve Phase 2B.

## What must never be included

Artifact bundles must not contain:

- public endpoint URLs,
- secret signing material,
- seed phrases,
- reusable invocation payloads,
- bundled transaction payloads,
- replayable exploit procedures,
- live victim targeting lists,
- public-network portable attack artifacts.

If any artifact contains unsafe content, the bundle reviewer marks that artifact as blocked and omits the raw
content from its report.

## Bundle manifest format

A bundle manifest is optional. It can reference local paths only:

```yaml
artifacts:
  live_fork_check: live_fork_check.md
  aave_readonly_discovery: aave_readonly_discovery.md
  evidence_pack: aave_v3_evidence_pack.md
  target_manifest: aave_v3_readonly.yaml
  dependency_graph_review: dependency_graph_review.md
  target_manifest_review: target_manifest_review.md
  manual_live_smoke: manual_live_fork_smoke_result.md
  phase2b_preflight: phase2b_preflight.md
  evidence_quality_report: live_fork_evidence_quality_report.md
```

Relative paths are resolved from the manifest directory.

## Running the live artifact bundle review

Review an artifact directory:

```bash
python scripts/review_live_artifact_bundle.py \
  --artifact-dir artifacts \
  --output docs/live_artifact_bundle_review.md
```

Review an explicit manifest:

```bash
python scripts/review_live_artifact_bundle.py \
  --bundle-manifest artifacts/live_artifact_bundle.yaml \
  --output docs/live_artifact_bundle_review.md
```

Run deterministic fixture-demo mode for CI:

```bash
python scripts/review_live_artifact_bundle.py \
  --fixture-demo \
  --output /tmp/live_artifact_bundle_review.md
```

The script only reads files. It does not run discovery automatically unless `--fixture-demo` is explicitly
requested, and fixture-demo uses existing fixture-backed evidence generation.

## Verdict interpretation

Phase 2A.6 verdicts are review verdicts only:

- `REVIEW_INCOMPLETE` means required evidence is missing, malformed, unsafe, or not sufficiently classified.
- `FIXTURE_ONLY_NOT_EXECUTION_READY` means deterministic CI evidence exists, but no live-local readiness claim
  can be made.
- `LIVE_READONLY_EVIDENCE_REVIEW_READY` means user-provided localhost read-only evidence can be reviewed.
  It is not execution approval.
- `BLOCKED_FOR_PHASE_2B` means blockers remain and execution must stay disabled.

There is no Phase 2A.6 execution-ready verdict.

## Relationship to existing evidence quality review

The live artifact bundle reviewer identifies safe artifacts that can feed the existing Phase 2A.6 evidence
quality review path:

- evidence pack,
- target manifest,
- dependency graph review,
- optional manual live smoke result,
- optional Phase 2B preflight output.

The bundle review does not duplicate the evidence-quality engine and does not create a parallel framework.
It bridges user-provided files into `review_evidence_quality()` when the required safe inputs exist.

## Phase 2B remains disabled

A successful live artifact bundle review can improve evidence quality and triage. It cannot enable executable
fork drills. Phase 2B remains blocked unless a later, explicit, separately approved gated execution PR changes
that behavior.
