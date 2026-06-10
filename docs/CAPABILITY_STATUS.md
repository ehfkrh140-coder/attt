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
