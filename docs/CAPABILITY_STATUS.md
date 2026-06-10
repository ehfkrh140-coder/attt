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
