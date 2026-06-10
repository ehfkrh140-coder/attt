# DeFi Defense Simulation Lab

A defensive research framework for validating DeFi controls with executable, isolated local drills.

The lab is **not** a public-network attack tool and is **not** a text-only scenario generator. The current MVP runs in a MockArena, changes local state, lets Blue observe only blind safe features, and evaluates results with snapshots, state diffs, invariants, and impact assertions.

## Current supported MVP

Supported now:

- MockArena executable local drills.
- Recon from `TargetProtocolSpec`.
- Blind Blue defense with no Red answer labels.
- Multi-mode evaluation: `defense_first`, `red_first`, `gas_priority`, `private_orderflow`, and `randomized_seeded`.
- Regression suite across core mock drills and ordering modes.
- Scorecards for Recon, Red, Blue, Safety, and Evaluation quality.
- Safe reports and safe beginner summaries.
- GitHub Actions CI for tests and the demo entrypoint.

Not supported yet:

- Real mainnet execution.
- Public RPC transactions.
- Real private keys.
- Real Aave or Haedal adapters.
- Real EVM fork drill execution.
- Real Sui localnet drill execution.

## Flow

```text
TargetProtocolSpec
→ Recon Intelligence
→ RiskHypothesis / InvariantSpec
→ Executable Local Red Drill
→ Blind Blue Defense
→ State-Diff / Invariant Evaluation
```

## Quick start

```bash
pip install -e ".[test]"
pytest -q
python main.py
```

`python main.py` prints a beginner-readable score summary. It is MockArena-only and does not print raw payloads, keys, or reusable attack details.

## GitHub Actions

After pushing a branch or opening a pull request, check the **Actions** tab for the `tests` workflow. It installs the test extra, runs `pytest -q`, and runs `python main.py`.

## Safety boundary

- Bots may connect only to local execution paths.
- Executable drills require `scope_confirmed=true` and in-scope targets.
- Red and Blue execute transactions only through Arena abstractions.
- Reports store safe labels, never raw reusable exploit calldata.
- EVM/Sui executable adapters are gated until real isolated adapters exist.

## More documentation

- Beginner runbook: `docs/BEGINNER_RUNBOOK.md`
- Capability status: `docs/CAPABILITY_STATUS.md`

## Protocol Twin and External World Twin

An EVM Fork Twin copies on-chain protocol state into a local fork for EVM targets such as Aave V3. That local fork is only one part of realistic testing: it does not automatically reproduce live mempool activity, keeper timing, future oracle updates, offchain APIs, bridge remote-chain state, frontend behavior, liquidation or arb bot timing, or congestion.

The External World Twin fills those gaps with local-only emulation. It can model local orderflow, private-orderflow visibility gaps, delayed keepers, stale oracle windows, liquidity shocks, bridge message stubs, offchain-data stubs, user-intent bursts, gas priority pressure, block delay, and timestamp jumps.

The Twin Fidelity Score reports what was copied, what was emulated, what was missing, and how much confidence to place in the result. Missing components are reported honestly instead of hidden.

Aave V3 follows the EVM Fork Twin target path. Haedal/Sui remains gated until a real Sui state twin adapter exists. MockArena remains the regression and learning mode. Users do not manually design Red scenarios: Recon and the auto runner select drills from target and environment conditions.

## Protocol Twin CLI examples

```bash
python scripts/run_protocol_twin.py --protocol mock_lending
python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum --fork-block latest
python scripts/create_protocol_twin.py --protocol aave_v3 --network ethereum --root-address <root-address> --fork-block latest
python scripts/run_protocol_twin.py --protocol haedal
```

`mock_lending` runs the full MockArena simulation. `aave_v3` follows the EVM Fork Twin path and reports missing root or gated execution status when needed. `haedal` reports unsupported Sui adapter status until a real Sui state twin adapter exists.

## MockArena MVP Release Verification

Run these commands before treating v0.1.0 as ready:

```bash
pip install -e ".[test]"
pytest -q
python main.py
python scripts/run_protocol_twin.py --protocol mock_lending
python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum
python scripts/run_protocol_twin.py --protocol haedal
python scripts/verify_mvp.py
```

Expected behavior:

- `mock_lending` runs the executable MockArena simulation.
- `aave_v3` reports the EVM Fork Twin path and a missing-root or gated/read-only status.
- `haedal` reports Sui State Twin unsupported/gated status.
- `verify_mvp.py` checks release readiness and prints `Overall: PASS` when local checks pass.
- GitHub Actions should show a green `tests` workflow after push or pull request.

## Phase 2A EVM Fork Twin read-only status

Phase 2A adds read-only EVM Fork Twin discovery for Aave V3 root-address onboarding. It can validate a local fork RPC setting, read safe local-fork labels for PoolAddressesProvider, Pool, PoolConfigurator, PriceOracle, and ACLManager, build a partial `TargetProtocolSpec`, run Recon, and list planned Red drill recommendations as gated.

Phase 2A still does not execute EVM fork Red drills, does not run a live fork mempool defender, does not send transactions, does not use private keys, and does not implement a real Aave defense bot. MockArena remains separate as the executable local regression path.
