# Phase 2B Preflight

Phase 2B remains blocked. This document explains the evidence a reviewer must collect before any future mediated local fork execution design can move beyond the disabled state.

This is not execution support. It does not send transactions, does not require signing, and does not enable executable EVM fork Red drills.

## Why Phase 2B is blocked

Phase 2A proved the read-only path in CI with fixtures and provided optional manual checks for a user-run local fork. Before Phase 2B can start, a reviewer must prove that read-only discovery works in the user's own local fork environment and that the target scope has been reviewed.

Phase 2B is blocked until all of these are available:

- A recorded manual live local fork smoke result.
- A reviewed target manifest.
- A dependency graph review.
- A reviewed fork execution policy.
- An approved harmless first drill candidate.
- A snapshot and rollback plan.
- Confirmation that fork execution remains disabled by default.

## Files required for preflight

The default preflight command looks for:

- `docs/manual_live_fork_smoke_result.md`
- `targets/generated/aave_v3_readonly.yaml`
- `docs/dependency_graph_review.md`

You may pass different local file paths to the preflight script. These files are review artifacts only; this preflight does not enable execution.

## Manual steps before preflight

1. Start a local fork yourself using your own local tooling.
2. Check that this project can read the local endpoint only.
3. Run Aave V3 read-only discovery with a root address.
4. Record the result with `scripts/record_live_fork_smoke_result.py`.
5. Export or provide a reviewed target manifest.
6. Write a dependency graph review.
7. Run `scripts/phase2b_preflight.py`.

No upstream endpoint, secret, reusable payload, or selector should be written into these files.

## Example commands

```bash
python scripts/record_live_fork_smoke_result.py \
  --output docs/manual_live_fork_smoke_result.md \
  --date 2026-06-10 \
  --local-fork-tool local-tool \
  --fork-block reviewed-block \
  --local-rpc-url http://127.0.0.1:8545 \
  --chain-id 31337 \
  --root-address local-root-address-label \
  --discovery-status partial \
  --discovered-contracts Pool,PriceOracle \
  --unresolved-calls ACLManager \
  --reviewer reviewer-name \
  --notes local-read-only-smoke \
  --no-transaction-sent-confirmation yes

python scripts/phase2b_preflight.py
```

If required artifacts are missing, the preflight should report `Phase 2B readiness: FAIL`. That is safe and expected until the review evidence exists.

## Review requirement

A reviewer must confirm that the manifest scope is safe before any future execution mode is considered. Even with all files present, this repository still keeps fork execution disabled and `EvmForkExecutionArena.execute_local_intent` unsupported.
