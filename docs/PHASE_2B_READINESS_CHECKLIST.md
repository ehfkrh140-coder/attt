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
