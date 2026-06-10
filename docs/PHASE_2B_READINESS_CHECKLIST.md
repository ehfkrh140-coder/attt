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

## Concrete design gates added before implementation

- [ ] manual_live_fork_smoke_result.md exists and is reviewed.
- [ ] reviewed_target_manifest exists. Reviewed target manifest exists.
- [ ] Dependency graph review exists.
- [ ] Fork execution policy has been reviewed.
- [ ] First drill candidate has been approved.
- [ ] explicit enable flag absent by default. Explicit enable flag is absent by default.
- [ ] CI still does not run live fork execution.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises `UNSUPPORTED_EXECUTABLE_FORK_DRILLS` until implementation approval.

## Live-smoke support preflight gates

- [ ] `scripts/record_live_fork_smoke_result.py` has been used to create a safe manual smoke record.
- [ ] `scripts/phase2b_preflight.py` reports missing prerequisites until review artifacts exist.
- [ ] `docs/PHASE_2B_PREFLIGHT.md` has been read by the reviewer.
- [ ] The target manifest remains unconfirmed unless a reviewer explicitly confirms scope.
- [ ] Fork execution mode is still disabled by default.
- [ ] `EvmForkExecutionArena.execute_local_intent` still raises `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.
