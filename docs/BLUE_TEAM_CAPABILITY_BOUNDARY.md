# Blue Team Capability Boundary — Phase 2A.5-R

## Definition

Blue Team = the blind defender that receives Recon-derived risk context and live arena observables, then takes local-only emergency actions to preserve invariants.

Blue must be powerful but blind.

## Blue can see

- Recon risk context
- attack surface map
- dependency graph
- invariant catalog
- recent state window
- blind observables
- target category
- call shape
- sender profile
- timing pattern
- dependency context
- state delta hints
- visibility mode
- ordering hints
- vault/reserve/accounting deltas
- identity mismatch indicators

## Blue must not see

- Red drill name
- exploit label
- exact Red path
- Red success condition
- privileged evaluator answer

## Strong local defense actions Blue may model

- local-only block
- local-only pause
- local-only quarantine
- local-only circuit breaker
- local-only dependency isolation
- local-only emergency governance simulation
- local-only risk parameter adjustment
- local-only vault outflow guard
- local-only canonical identity enforcement
- local-only incident evidence generation

## Permanently forbidden Blue behavior

- public network transaction execution
- public RPC execution as a bot
- real admin key usage
- real protocol intervention
- live victim tracking
- public mempool defense bot behavior
- scope escape

## Success and failure

Blue success is judged by invariant preservation, state-diff improvement, blast-radius reduction, response timeliness, correct blind detection, and absence of Red-label leakage.

Blue failure includes alert-only behavior when block/quarantine is required, relying on UI-hidden status as security, missing canonical identity mismatch, missing residual asset risk, treating multi-pool same-pattern incidents as unrelated, or using leaked Red labels/exact paths.
