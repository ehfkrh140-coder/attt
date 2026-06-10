# Recon Capability Boundary — Phase 2A.5-R

## Core principle

**Red가 최강이려면 Recon은 더 최강이어야 한다.**

**For Red to be world-class, Recon must be stronger than Red.**

Recon is a first-class adversarial discovery engine, not a report generator.

## Definition

Recon = the engine that converts protocol reality into:

1. vulnerability hypotheses
2. local-only Red drill candidates
3. Blue blind observables
4. Evaluator invariant checks
5. evidence requirements
6. external-world twin gaps

Recon must not merely describe risks. Recon must discover risk surfaces that can be tested.

## Required discovery surfaces

Recon must discover from:

- protocol state
- ABI compatibility
- contract/account/program graph
- reserve/vault/asset/accounting graph
- permission and authority graph
- dependency and staleness graph
- canonical identity binding
- stale / retired / UI-hidden surfaces
- residual asset surfaces
- oracle / keeper / external dependency gaps

## Allowed now inside the sealed lab

- full local fork / local twin read access
- manifest-scoped graph expansion
- ABI compatibility probing
- storage/account layout inference
- canonical asset identity analysis
- reserve/vault/accounting analysis
- permission/authority analysis
- dependency staleness analysis
- invariant mining
- local-only probe planning
- synthetic state candidate planning
- Red drill candidate synthesis
- Blue observable synthesis
- Evaluator invariant synthesis

## Future gated Recon permissions

Only after a sealed execution harness exists:

- snapshot/revert-controlled active probing
- local-only transaction simulation
- local-only abnormal account graph construction
- local-only synthetic attacker account construction
- local-only synthetic attacker mint construction
- local-only dependency failure construction
- local-only adversarial external-world pressure discovery

## Permanently forbidden Recon behavior

- public active probing
- public RPC active execution
- public mempool observation
- live victim targeting
- scope escape
- real key use
- real fund movement
- replayable exploit output

## Finding sufficiency rule

A Recon finding is insufficient if:

- it is narrative-only
- it has no invariant at risk
- it has no evidence requirement
- it cannot produce a local-only Red drill candidate or probe plan
- it gives Blue no blind observable
- it gives Evaluator no state-diff or invariant-diff check
- it lacks a safety containment requirement
