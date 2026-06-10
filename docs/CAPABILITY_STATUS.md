# Capability Status

| Capability | Status | Notes |
|---|---|---|
| MockArena executable drills | Supported | Current MVP runtime for local state-changing drills |
| Blind Blue defense | Supported | Uses blind features and no Red answer labels |
| Multi-mode evaluation | Supported | defense_first, red_first, gas_priority, private_orderflow, randomized_seeded |
| Scorecards | Supported | Recon, Red, Blue, Safety, and Evaluation quality scores |
| GitHub Actions CI | Supported | Runs pytest and the main demo |
| EVM Fork adapter | Gated / Not implemented | Placeholder only; executable support is blocked until a real isolated adapter exists |
| Sui Localnet adapter | Gated / Not implemented | Placeholder only; executable support is blocked until a real isolated adapter exists |
| Public network execution | Not supported | Intentionally forbidden by the safety boundary |
| Real private keys | Not supported | Intentionally forbidden by the safety boundary |
| Real Aave adapter | Not implemented | Future work only; not part of the MockArena MVP |
| Real Haedal adapter | Not implemented | Future work only; not part of the MockArena MVP |
| Protocol Twin onboarding | Partial | MockArena works; EVM Fork Twin is read-only/gated until adapter readiness |
| External World Twin | Supported locally | Emulates orderflow, keepers, oracle timing, liquidity, bridge stubs, offchain stubs, user intents, and network conditions |
| Twin Fidelity Score | Supported | Reports copied/emulated/missing coverage honestly |
| Aave V3 path | Gated / read-only planning | Uses EVM Fork Twin path and never silently falls back to mock |
| Haedal path | Gated / Not implemented | Sui state twin adapter is not implemented |
