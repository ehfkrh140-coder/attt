# Raydium-style LP Mint Validation Case — Defensive Local-only Design

Date: 2026-06-10

Case family: `CanonicalAssetIdentityFailure`

Design-only drill candidate: `ForgedLPMintRetiredPoolDrainDrill`

## Safety boundary

This is a defensive local-only simulation design case. It does not add live Raydium interaction, Solana mainnet interaction, attacker reproduction steps, raw transaction details, live account targeting, public-network procedure, or replayable exploit artifacts.

## Design principles

- UI-hidden or retired pool status is not security.
- Residual vault assets remain attack surface.
- LP mint identity must be strongly bound to canonical pool state.
- User token account mint must match canonical LP mint.
- Vault outflow must correspond to canonical LP burn/accounting.
- Dependency shutdown must not create withdrawal bypass.
- Multi-pool same-pattern findings must be evaluated as campaign risk.

## Recon should detect

- retired pool surface
- UI-hidden but callable surface
- residual vault assets
- canonical LP mint binding weakness
- token account mint mismatch
- dependency tombstone / stale dependency
- multi-pool same-pattern exposure

## Red should model locally

- synthetic attacker mint
- synthetic token account graph
- non-canonical LP mint submission
- retired/stale pool interaction
- local-only multi-pool campaign

These are sealed-lab abstractions only, not public reproduction steps.

## Blue should respond locally

- canonical LP mint enforcement
- suspicious mint rejection
- retired pool quarantine
- vault outflow circuit breaker
- dependency isolation
- emergency local pause
- campaign-level escalation

## Evaluator should check

- fake LP mint accepted or rejected
- vault outflow allowed or blocked
- canonical LP burn/accounting relationship
- residual asset protection
- Blue label leakage
- campaign-level grouping
- state diff
- invariant diff

## Invariant framing

A fake LP mint acceptance in this design case is an invariant failure because canonical LP mint identity and vault-accounting burn relationships are not preserved. UI-hidden status alone is never a valid security boundary, and multi-pool same-pattern findings must be grouped as campaign risk.
