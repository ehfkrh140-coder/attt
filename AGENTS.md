# AGENTS.md

## Project Identity

This repository is a defensive, isolated DeFi security simulation lab.

It is not a public-network attack tool.
It is not a text-only scenario generator.

The system evaluates DeFi defenses by running executable local adversarial drills inside an isolated Mainnet Fork, localnet, or mock arena.

## Core Principle

A Defender Bot is meaningful only if it is tested against real executable local drills.

Static virtual scenarios are not sufficient.
Text-only Red Team scenarios are not accepted as security validation.

The correct flow is:

TargetProtocolSpec
→ Recon Intelligence
→ RiskHypothesis / InvariantSpec
→ Executable Local Red Drill
→ Blind Blue Defense
→ State-Diff / Invariant Evaluation

## Public-Network Safety Boundary

The project must never:

- broadcast transactions to public networks,
- connect bot execution paths directly to public RPC endpoints,
- perform public mempool front-running,
- use real private keys,
- move real funds,
- generate public-network portable exploit artifacts,
- save raw reusable exploit calldata in reports,
- target contracts outside confirmed scope.

## Local Execution Requirement

The project must support:

- isolated Mainnet Fork execution,
- isolated localnet execution,
- mock protocol execution,
- local pending transaction simulation,
- Red executable local drills,
- Blue real-time local defense,
- Evaluation based on local state diffs and invariant checks.

## Fork Upstream Rule

A fork node may use an upstream archive RPC only to hydrate local fork state.

Bots must connect only to localhost or 127.0.0.1.
Bots must not send transactions to upstream RPC.
Bots must not directly connect to public RPC.

## Target Scope Rule

Executable drills require a confirmed TargetProtocolSpec.

A protocol name alone may start target resolution, but it must not allow executable drills until:

- in-scope contracts are confirmed,
- runtime adapter exists,
- arena is local,
- SafetyGuard passes,
- scope_confirmed=true.

## Recon Requirements

Recon must be target-specific.

Recon must produce:

- AttackSurfaceMap
- ContractGraph
- DependencyGraph
- CriticalPath
- InvariantSpec
- RiskHypothesis
- RedDrillRecommendation
- BlueControlRecommendation

Recon must not produce only generic DeFi warnings.

## Red Team Requirements

Red Team is not a text scenario generator.
Red Team is not a dummy attacker.

Red Team must produce ExecutableDrill objects.

Each ExecutableDrill must:

- derive from a Recon RiskHypothesis,
- run only inside an approved local arena,
- attempt to trigger a real local invariant failure,
- provide blind observables to Blue,
- provide hidden ground truth only to Evaluation,
- support snapshot/revert,
- pass SafetyGuard,
- avoid public-network portable artifacts.

A Red challenge without ExecutableDrill and ImpactAssertion is invalid.

## Extreme Local Drill Requirement

Within the approved isolated arena, Red Team drills must be strong enough to stress Blue to its limits.

Do not replace executable local drills with dummy payloads.
Do not reduce complex local state transitions to static text.
Do not make every Red drill easy to decode with one function selector.

Red may use only arena-contained, non-portable mechanisms to test Blue under stress:

- local call-graph indirection using allowlisted mock wrappers,
- local pending transaction ordering pressure,
- local benign decoy traffic,
- local state warping through audited Arena methods,
- local multi-stage risk composition,
- local boundary-value and invariant probes,
- local liquidity exhaustion stress,
- local governance/admin permission-boundary probes.

These mechanisms must not be portable to public networks and must not be emitted as raw reusable exploit recipes.

## Blue Team Requirements

Blue must defend against executable local drills.

Blue must:

- observe local pending tx or local arena events,
- decode safe features,
- combine Recon context and live signals,
- classify threat,
- select DefenseAction,
- pass SafetyGuard,
- act before or during local drill execution when possible.

Blue must not see Red ground truth.

## Evaluation Requirements

Evaluation must use:

- pre-drill snapshot,
- local pending tx trace,
- Blue action trace,
- post-drill snapshot,
- invariant checks,
- ImpactAssertion.

Evaluation must score:

- Recon quality,
- Red drill quality,
- Blue defense quality,
- Safety compliance.

## Non-Negotiable Tests

The test suite must prove:

- static Red scenarios are rejected,
- Recon requires TargetProtocolSpec,
- protocol-name-only mode cannot execute drills,
- Red drills only execute in local arenas,
- Blue cannot access ground truth,
- Blue can block at least one executable local drill,
- Red can produce extreme but contained local stress drills,
- SafetyGuard blocks public RPC,
- Evaluation uses state diffs and invariants, not text labels.

## If Unsure

Choose containment, not deletion.

Do not remove executable local drills.
Instead, ensure they are fork-bound, local-only, scoped, non-exportable, and SafetyGuard-protected.
