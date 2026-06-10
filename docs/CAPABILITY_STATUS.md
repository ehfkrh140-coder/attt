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
