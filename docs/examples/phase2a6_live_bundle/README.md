# Phase 2A.6 Safe Live-Review Sample Bundle

This directory is a deterministic, safe sample for the Phase 2A.6 live artifact
bundle reviewer. It is designed for CI and reviewer walkthroughs.

The bundle represents user-provided localhost read-only evidence. It is not proof
that a live local fork was run by the current reviewer. It does not grant Phase
2B execution permission.

Run directory review:

```bash
python scripts/review_live_artifact_bundle.py \
  --artifact-dir docs/examples/phase2a6_live_bundle \
  --output /tmp/phase2a6_example_bundle_review.md
```

Run manifest review:

```bash
python scripts/review_live_artifact_bundle.py \
  --bundle-manifest docs/examples/phase2a6_live_bundle/live_artifact_bundle.yaml \
  --output /tmp/phase2a6_example_bundle_manifest_review.md
```

Expected result: review-ready local evidence may be classified, but execution
permission remains `no` and Phase 2B remains disabled.
