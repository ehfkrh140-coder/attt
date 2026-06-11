# No-Fake-Scenario Standard

## Required principle

No drill may pass based only on narrative.
No Recon finding may pass based only on narrative.
No Blue defense may pass based only on an alert.
No Evaluator verdict may pass without state-diff or invariant-diff evidence.

## Maturity levels

| Level | Meaning | Status |
|---|---|---|
| L0 | story-only scenario | insufficient |
| L1 | static fixture scenario | useful for CI, insufficient for high-confidence defense claims |
| L2 | ABI/account/graph-compatible finding | acceptable for planning |
| L3 | local state transition in MockArena or local twin | minimum for real defense evaluation |
| L4 | sealed fork/local validator execution with snapshot/revert | Phase 2B target |
| L5 | external-world twin pressure with adversarial ordering, keeper/oracle/mempool/congestion simulation | long-term target |

## No-Fake pass criteria

A finding or drill must include:

- affected surface
- invariant at risk
- local execution or simulation path
- expected state transition
- Blue blind observable
- Evaluator check
- evidence requirement
- safety containment proof

## Blue standard

When an invariant requires block, pause, quarantine, circuit breaker, or dependency isolation in the sealed lab, an alert-only Blue response is insufficient.

## Evaluator standard

Evaluator verdicts require state-diff or invariant-diff evidence and must verify Red-label leakage did not occur.
