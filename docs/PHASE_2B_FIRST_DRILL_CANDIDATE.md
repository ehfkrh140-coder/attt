# Phase 2B First Drill Candidate

Not an exploit. Not a real attack. Not a fund-moving drill.

## Candidate: fork snapshot/revert and liveness sentinel

The first Phase 2B candidate should verify the local fork execution harness without moving assets or changing protocol economics.

Allowed shape:

- Capture a baseline read-only state snapshot.
- Create an Arena snapshot.
- Perform a dry-run circuit-breaker intent or mock-local no-op sentinel event through the Arena interface.
- Revert to the snapshot.
- Re-read target liveness and compare to baseline.

## Hard restrictions

- `value=0`.
- No token transfer.
- No approval.
- No liquidation.
- No borrow.
- No withdrawal.
- No governance execution.
- No oracle manipulation.
- No asset movement.
- No public RPC.
- No private keys.

## Approval requirement

This candidate must be reviewed and explicitly approved after the Phase 2B readiness checklist is complete. Until then, it remains design-only.
