# Capability Status

| Capability | Status | Notes |
|---|---|---|
| MockArena executable simulation | Supported | Current v0.1.0 MVP runtime for local state-changing drills |
| MockArena executable drills | Supported | Current MVP runtime for local state-changing drills |
| Blind Blue defense | Supported | Uses blind features and no Red answer labels |
| Multi-mode evaluation | Supported | defense_first, red_first, gas_priority, private_orderflow, randomized_seeded |
| Protocol Twin onboarding scaffold | Supported | Distinguishes MockArena, EVM Fork Twin, and Sui State Twin modes |
| External World Twin local emulation | Supported | Emulates orderflow, keepers, oracle timing, liquidity, bridge stubs, offchain stubs, user intents, and network conditions |
| Twin Fidelity Score | Supported | Reports copied/emulated/missing coverage honestly |
| Scorecards | Supported | Recon, Red, Blue, Safety, and Evaluation quality scores |
| GitHub Actions CI | Supported | Runs install, pytest, main demo, and MVP verifier |
| Beginner-safe CLI summary | Supported | `main.py` and verifier output are sanitized |
| EVM Fork Twin read-only/gated planning | Partial / Gated | Aave V3 path is recognized, but executable fork drills are blocked until adapter readiness |
| Aave V3 fork-twin onboarding path | Partial / Gated | Uses EVM Fork Twin path and never silently falls back to mock |
| EVM Fork adapter | Gated / Not implemented | Placeholder only; executable support is blocked until a real isolated adapter exists |
| Sui Localnet adapter | Gated / Not implemented | Placeholder only; executable support is blocked until a real isolated adapter exists |
| executable EVM fork Red drills | Unsupported / Not implemented | Intentionally gated for this release |
| real Aave adapter | Unsupported / Not implemented | Future work only; not part of v0.1.0 |
| Sui State Twin | Unsupported / Not implemented | Gated until a real Sui adapter exists |
| real Haedal adapter | Unsupported / Not implemented | Future work only; not part of v0.1.0 |
| Haedal path | Gated / Not implemented | Sui state twin adapter is not implemented |
| Public network execution | Not supported | Intentionally forbidden by the safety boundary |
| Real private keys | Not supported | Intentionally forbidden by the safety boundary |
| EVM Fork Twin read-only discovery scaffold | Supported | Validates local fork settings and performs safe read-only discovery |
| Aave V3 root-address read-only resolver | Supported | Discovers Pool, PoolConfigurator, PriceOracle, and ACLManager when local read data is available |
| Recon on read-only TargetProtocolSpec | Supported | Runs Recon on partial read-only EVM target specs |
| live fork mempool defense | Unsupported / Not implemented | Future phase only |
| real transaction execution | Unsupported / Not implemented | Intentionally blocked |
| real Aave defense bot | Unsupported / Not implemented | Future phase only |
| EVM local JSON-RPC read-only transport | Supported in Phase 2A.1 | Localhost-only reads: chain id, code, read-only calls, storage, and balance. |
| Aave V3 local-fork read-only discovery | Partial / Gated | Requires a user-provided local fork and root address; executable drills remain gated. |
| Executable Aave fork drills | Not implemented | Phase 2A.1 is read-only only. |
| Local fork transaction sending | Not supported | Read-only transport blocks send, sign, wallet, debug, txpool, and local mutation RPC methods. |
| Local fork smoke script | Supported in Phase 2A.2 | Checks localhost fork reachability using read-only calls only. |
| Aave V3 read-only discovery script | Supported in Phase 2A.2 | Requires local fork plus root address; reports partial/unavailable safely. |
| Live local fork transactions | Not supported | Smoke tooling is read-only and keeps execution gated. |
| Safe read-only target export | Supported in Phase 2A | Exports unconfirmed Aave read-only TargetProtocolSpec manifests without executable scope. |
| Phase 2B executable fork drills | Future work | Not implemented in Phase 2A; local fork execution remains gated. |
| Phase 2A depth audit | Supported | Documents fixture-backed CI, optional live local fork manual checks, and remaining limits. |
| Manual live local fork smoke | Optional / Manual | User-run localhost-only read-only smoke; not run by CI. |
| Phase 2B readiness checklist | Supported | Blocks executable fork work until live read-only and safety prerequisites are reviewed. |
| Phase 2B fork execution design | Design only | Policy and Arena interfaces exist, but execution is disabled. |
| EVM fork execution arena | Gated placeholder | `execute_local_intent` raises unsupported until Phase 2B approval. |
| First harmless fork drill candidate | Design only | Snapshot/revert and liveness sentinel; no asset movement. |

## Phase 2B Preflight Support

Phase 2B is still blocked and design-only. The new live-smoke support tools help a reviewer record manual read-only evidence before any future execution work is considered.

- `python scripts/record_live_fork_smoke_result.py ...` writes a safe markdown record from reviewed local-only fields.
- `python scripts/phase2b_preflight.py` checks that the manual smoke record, reviewed target manifest, and dependency graph review exist.
- The preflight is expected to report `Phase 2B readiness: FAIL` until every review artifact is present.
- Fork execution remains disabled by default, no transactions are sent, and executable EVM fork Red drills remain unsupported.
- Do not include upstream endpoints, secrets, reusable payloads, or raw selectors in any preflight artifact.

## Phase 2A.4 Read-only Aave Reserve Metadata

Aave V3 read-only discovery now attempts to read reserve metadata from the local fork after the PoolAddressesProvider resolves the Pool. The resolver asks only safe named read calls for the reserve list, per-reserve data, reserve configuration, asset price, oracle source, and ACL role labels, then feeds the discovered reserve assets, aToken/debt-token relationships, watch items, and basic configuration flags into Recon.

The default reserve limit is 8. A user may request a different limit, but the resolver enforces a hard cap of 50 and reports whether truncation occurred. Discovery may be full, partial, decode-unavailable, or unavailable depending on what the local fork returns. The result is still read-only: no transactions are sent, Red drills are recommendation-only, MockArena is not used as Aave fallback, and Phase 2B execution remains blocked.

## Phase 2A.5 evidence workflow status

- Live local fork evidence pack: available as a read-only review workflow.
- Fixture evidence pack: available for CI and release verification only; it is not enough for Phase 2B.
- Target manifest review: parses generated manifests and checks read-only flags, but does not confirm scope automatically.
- Dependency graph review: generated from Recon output and reserve metadata; it is a review candidate, not execution permission.
- Phase 2B execution: still blocked and disabled. No transactions are sent and no Aave Red drills run.

## Phase 2A.5-R Recon / Red / Blue Extreme Capability Reframe

The capability model now uses this permanent rule:

> External public-world behavior is forbidden. Internal sealed-lab equivalents must be modeled with maximum realism.

> 외부 세계에서는 금지한다. 내부 실험실에서는 현실과 똑같이, 오히려 더 극한적으로 구현한다.

> Red가 최강이려면 Recon은 더 최강이어야 한다.

> For Red to be world-class, Recon must be stronger than Red.

Forbidden public-world capabilities are not described as missing features. They are **forbidden outside** and **modeled inside** through sealed-lab equivalents.

### Permanent forbidden capabilities

- public network active probing
- public network transaction broadcast
- public RPC through Red/Blue execution
- live victim targeting
- public mempool observation for attack discovery
- real private key usage
- real fund movement
- out-of-scope contract/program exploration
- replayable exploit package generation
- raw reusable calldata / transaction bundle output
- public-network portable exploit artifacts

### Current Phase 2A limitations

- EVM fork and Aave V3 support remain read-only discovery, planning, evidence, and preflight review.
- Red can execute MockArena drills, but executable EVM fork Red drills remain disabled.
- Blue can defend in local arenas and consume blind observables, but does not operate as a public-network bot.
- Phase 2B execution remains blocked; `EvmForkExecutionArena.execute_local_intent()` still raises `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

### Future sealed-local capabilities after explicit gates

- Recon: snapshot/revert-controlled local active probing, local-only transaction simulation, synthetic account/mint construction, dependency failure construction, adversarial external-world pressure discovery.
- Red: sealed local fork transaction execution, local-only signer use, local-only impersonation, synthetic attacker mints/accounts, manifest-scoped retired/stale target interaction, local-only multi-pool campaigns, adversarial ordering, private-orderflow simulation.
- Blue: local-only pause, quarantine, circuit breaker, dependency isolation, emergency governance simulation, risk parameter adjustment, vault outflow guard, canonical identity enforcement, and incident evidence generation.

These future capabilities are policy and design targets only until a separate Phase 2B PR explicitly opens the sealed execution harness.

## Phase 2A.6 Live Fork Evidence Quality & ABI Compatibility Review

Phase 2A.6 adds a read-only evidence quality review layer over the Phase 2A.5 evidence workflow. It consumes an evidence pack, exported target manifest, dependency graph review, and optional manual live fork smoke record, then produces a sanitized markdown quality report.

Supported in Phase 2A.6:

- Evidence source classification: fixture-backed, live-local, live-local-unavailable, missing, or unknown.
- Evidence completeness findings for evidence pack, target manifest, dependency graph review, and optional manual live smoke result.
- ABI compatibility and decode quality review from existing read-only discovery evidence.
- Aave reserve coverage scoring and reserve gap triage.
- Dependency graph review quality checks.
- Target manifest review quality checks.
- Phase 2B blocker summary.
- Optional Phase 2B preflight output consumption as review evidence only.
- Safe markdown output at `docs/live_fork_evidence_quality_report.md`.

Still not supported:

- executable EVM fork Red drills
- transaction sending
- private key support
- public RPC Red/Blue execution
- Aave Red drills
- live Raydium/Solana/Aave interaction
- execution-ready verdicts

Phase 2A.6 verdicts are review verdicts only: `REVIEW_INCOMPLETE`, `FIXTURE_ONLY_NOT_EXECUTION_READY`, `LIVE_READONLY_EVIDENCE_REVIEW_READY`, or `BLOCKED_FOR_PHASE_2B`. There is intentionally no execution-approved verdict. Review success is not execution permission, and Phase 2B remains disabled.
