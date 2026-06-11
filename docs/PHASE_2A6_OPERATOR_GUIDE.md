# Phase 2A.6 Operator Guide — Live-Local Artifact Review

## Purpose

This guide helps an operator prepare a local-only, read-only artifact bundle for
Phase 2A.6 review. It is for evidence review and manual validation only. It does
not enable Phase 2B and does not approve execution.

## Required safety assumptions

- Use localhost, `127.0.0.1`, `::1`, or `mock://` endpoints only.
- Do not run Red or Blue execution through public RPC.
- Do not send transactions.
- Do not include private keys.
- Do not include raw calldata or transaction bundles.
- Do not include selectors, seed phrases, or reusable exploit artifacts.
- Do not include live victim targeting data.
- Do not include upstream public RPC URLs.
- Keep all artifacts inside the reviewed local artifact directory.

If any artifact violates these assumptions, discard it and regenerate sanitized
read-only evidence.

## Localhost-only requirement

A fork node may hydrate local fork state separately, but review artifacts should
only identify localhost or mock endpoints. Bots and review scripts must not
connect to public RPC. Phase 2A.6 review scripts only read files.

## Generate safe fixture artifacts

For CI or walkthroughs, use fixture-backed artifacts. Fixture-backed evidence is
useful for deterministic review, but it cannot approve Phase 2B.

```bash
python scripts/review_live_artifact_bundle.py \
  --fixture-demo \
  --output /tmp/live_artifact_bundle_review.md
```

The repository also includes a deterministic sample bundle:

```bash
python scripts/review_live_artifact_bundle.py \
  --artifact-dir docs/examples/phase2a6_live_bundle \
  --output /tmp/phase2a6_example_bundle_review.md
```

## Generate user-run live-local read-only artifacts

If the user has a localhost fork, generate artifacts with existing read-only
scripts and localhost endpoints only. The exact operator workflow may vary, but
artifacts should match the bundle convention in `docs/PHASE_2A6_LIVE_ARTIFACT_REVIEW.md`.

Suggested safe review sequence:

1. Run a localhost fork check and save a markdown result.
2. Run Aave V3 read-only discovery against localhost if the target is in scope.
3. Generate or export the live fork evidence pack.
4. Export the target manifest candidate.
5. Generate the dependency graph review.
6. Record a manual live fork smoke result.
7. Run Phase 2B preflight in review mode.
8. Assemble all files in one artifact directory.

Every command must remain read-only and localhost-only.

## Assemble an artifact directory

Use this deterministic layout when possible:

```text
artifact_dir/
  live_artifact_bundle.yaml
  aave_v3_evidence_pack.md
  aave_v3_readonly.yaml
  dependency_graph_review.md
  manual_live_fork_smoke_result.md
  phase2b_preflight.md
```

Optional files may include local fork check evidence, Aave read-only discovery
evidence, target manifest review, and a prior evidence quality report.

## Assemble a bundle manifest

A safe bundle manifest references local files only:

```yaml
artifacts:
  evidence_pack: aave_v3_evidence_pack.md
  target_manifest: aave_v3_readonly.yaml
  dependency_graph_review: dependency_graph_review.md
  manual_live_smoke: manual_live_fork_smoke_result.md
  phase2b_preflight: phase2b_preflight.md
```

Relative paths resolve from the manifest directory.

## Run the live artifact bundle review

Review by directory:

```bash
python scripts/review_live_artifact_bundle.py \
  --artifact-dir docs/examples/phase2a6_live_bundle \
  --output /tmp/phase2a6_example_bundle_review.md
```

Review by manifest:

```bash
python scripts/review_live_artifact_bundle.py \
  --bundle-manifest docs/examples/phase2a6_live_bundle/live_artifact_bundle.yaml \
  --output /tmp/phase2a6_example_bundle_manifest_review.md
```

## Run the evidence quality review

After the bundle identifies safe evidence pack, target manifest, and dependency
review inputs, run the existing evidence quality review if direct inspection is
needed:

```bash
python scripts/review_live_fork_evidence_quality.py \
  --evidence-pack docs/examples/phase2a6_live_bundle/aave_v3_evidence_pack.md \
  --target-manifest docs/examples/phase2a6_live_bundle/aave_v3_readonly.yaml \
  --dependency-graph-review docs/examples/phase2a6_live_bundle/dependency_graph_review.md \
  --manual-live-smoke-result docs/examples/phase2a6_live_bundle/manual_live_fork_smoke_result.md \
  --phase2b-preflight docs/examples/phase2a6_live_bundle/phase2b_preflight.md \
  --output /tmp/phase2a6_example_evidence_quality.md
```

## Interpret bundle review results

- `missing` means the artifact was not supplied.
- `fixture-backed` means deterministic CI evidence exists, but no live-local claim is proven.
- `live-local` means the artifact indicates localhost read-only workflow.
- `unknown` means the artifact is present but not classified strongly enough.
- `unsafe` means the artifact must be removed and regenerated safely.

The bundle review report includes operator next actions and still says execution
permission is not granted.

## Interpret evidence quality results

- `REVIEW_INCOMPLETE` means required evidence is missing or malformed.
- `FIXTURE_ONLY_NOT_EXECUTION_READY` means CI fixture evidence is useful but not execution-ready.
- `LIVE_READONLY_EVIDENCE_REVIEW_READY` means the evidence is review-ready only.
- `BLOCKED_FOR_PHASE_2B` means blockers remain.

None of these verdicts grants execution permission.

## Manual reviewer sign-off checklist

Before accepting a Phase 2A.6 live review packet, the reviewer should confirm:

- artifacts are local files only,
- endpoints are localhost or mock labels only,
- no unsafe secrets or reusable public-network artifacts are present,
- evidence pack, target manifest, dependency review, smoke result, and preflight were reviewed,
- evidence quality findings are understood,
- Phase 2B blockers are recorded,
- execution permission remains `no`.

## Unsafe artifacts

If an artifact is unsafe:

1. Do not copy its content into a report.
2. Remove it from the bundle.
3. Regenerate a sanitized read-only artifact from localhost workflow.
4. Re-run the bundle review.
5. Keep Phase 2B disabled.

## Missing or incomplete artifacts

If artifacts are missing or incomplete, keep the report as a review finding. Do
not invent evidence. Do not use fixture evidence to claim live-local readiness.

## Why review success is not execution permission

Phase 2A.6 evaluates evidence quality. It does not add execution gates, signer
support, transaction sending, Red/Blue public RPC execution, or executable fork
Red drills.

Phase 2B remains disabled until a separate explicitly approved gated execution
PR changes that status.
