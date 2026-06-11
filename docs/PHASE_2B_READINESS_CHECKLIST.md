# Phase 2B Readiness Checklist

Phase 2B must not begin until all checks below are complete.

- [ ] Live local fork manual smoke has been run by the user.
- [ ] Local fork read-only discovery works against a real fork.
- [ ] Aave root address is documented by a user-provided target manifest.
- [ ] Discovered Aave contracts and categories have been reviewed.
- [ ] Dependency graph review is done.
- [ ] SafetyGuard has a fork-execution mode design.
- [ ] Transaction execution remains local-only and arena-mediated.
- [ ] Red and Blue never connect to public RPC.
- [ ] No private keys are required or stored.
- [ ] Rollback/snapshot plan exists for every executable fork test.
- [ ] Initial fork execution drill is harmless and value=0.
- [ ] Defense action is mock/local circuit breaker only.
- [ ] Reports still avoid raw calldata, selectors, and reusable transaction payloads.
- [ ] CI continues to run fixture-backed tests without requiring a live fork.

If any item is incomplete, stay in read-only Phase 2A.


## Compatibility checklist tokens

These short checklist phrases are kept for existing release checks.

- [ ] manual_live_fork_smoke_result.md exists
- [ ] Reviewed target manifest exists
- [ ] Explicit enable flag is absent by default

## Concrete design gates added before implementation

- [ ] `manual_live_fork_smoke_result.md` exists and is reviewed.
- [ ] Reviewed target manifest exists.
- [ ] Dependency graph review exists.
- [ ] Fork execution policy has been reviewed.
- [ ] First drill candidate has been approved.
- [ ] Explicit enable flag is absent by default.
- [ ] CI still does not run live fork execution.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS` until implementation approval.

## Live-smoke support preflight gates

- [ ] `scripts/record_live_fork_smoke_result.py` created a safe smoke record.
- [ ] `scripts/phase2b_preflight.py` reports missing prerequisites until review
  artifacts exist.
- [ ] `docs/PHASE_2B_PREFLIGHT.md` has been read by the reviewer.
- [ ] Target manifest remains unconfirmed unless a reviewer confirms scope.
- [ ] Fork execution mode is still disabled by default.
- [ ] `EvmForkExecutionArena.execute_local_intent` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

## Phase 2A.5 evidence and review gates

- [ ] Live local fork evidence pack generated from localhost and reviewed.
- [ ] Fixture-only evidence explicitly rejected for Phase 2B readiness.
- [ ] Read-only TargetProtocolSpec manifest candidate reviewed.
- [ ] Generated manifest does not auto-confirm scope.
- [ ] Dependency graph review candidate generated from Recon and reserve metadata.
- [ ] Manual live fork smoke result recorded and reviewed.
- [ ] Phase 2B preflight run against evidence pack, manifest, and dependency review.
- [ ] Preflight output reviewed as review-ready only.
- [ ] Preflight output is not execution-enabled.
- [ ] Fork execution mode remains disabled.
- [ ] EvmForkExecutionArena still raises unsupported for local execution.

## Phase 2A.6-OP operator guide gates before Phase 2B

Phase 2A.6-OP adds operator guidance, a manual checklist, and deterministic safe
sample artifacts. It does not approve execution.

- [ ] `docs/PHASE_2A6_OPERATOR_GUIDE.md` has been read.
- [ ] `docs/PHASE_2A6_MANUAL_REVIEW_CHECKLIST.md` has been completed by reviewer.
- [ ] Sample bundle review passes by artifact directory when the live bundle reviewer is present.
- [ ] Sample bundle review passes by bundle manifest when the live bundle reviewer is present.
- [ ] Sample bundle reports remain sanitized.
- [ ] Review success is not treated as execution permission.
- [ ] No sample artifact is treated as proof of real live-local ABI compatibility.
- [ ] No public RPC Red/Blue execution exists.
- [ ] No executable fork drills exist.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.
