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

## Phase 2A.1 local EVM read-only transport

Phase 2A.1 adds a real JSON-RPC read-only transport for a local EVM fork. Start your local fork using your own local tooling. Bots and resolvers only connect to `http://127.0.0.1:8545` or `http://localhost:8545`; they do not connect to upstream providers directly.

For Aave V3 read-only discovery, provide the local fork URL and a PoolAddressesProvider/root address:

```bash
python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum --root-address <root-address> --local-rpc-url http://127.0.0.1:8545
```

Expected Phase 2A.1 behavior:

- If no local fork is running, the CLI reports `LOCAL_FORK_UNAVAILABLE` safely.
- If a local fork is running, the resolver performs read-only calls only and builds a partial `TargetProtocolSpec` for Recon.
- Executable EVM fork Red drills remain gated and do not run.
- MockArena remains a separate learning/regression mode and is never used as a silent fallback for an Aave V3 request.

## Phase 2A.2 live local fork read-only smoke

Phase 2A.2 adds beginner-friendly smoke scripts for a local EVM fork that you start separately with your own local tooling and upstream provider outside this project. This project only connects to localhost and only performs read-only JSON-RPC calls.

Check whether your local fork is reachable:

```bash
python scripts/check_local_evm_fork.py --local-rpc-url http://127.0.0.1:8545
```

Run Aave V3 read-only discovery after you have a PoolAddressesProvider/root address:

```bash
python scripts/aave_readonly_discovery.py --root-address <root-address> --local-rpc-url http://127.0.0.1:8545
```

If no local fork is running, `LOCAL_FORK_UNAVAILABLE` is a safe expected result. These scripts do not send transactions, do not use signing keys, do not execute Red drills, and do not silently fall back to MockArena for Aave V3.

## Phase 2A Read-only Local Fork Workflow

Phase 2A is the safe local-fork discovery workflow for EVM protocols. Start a local fork yourself with your own local tooling and upstream provider outside this project. This project only connects to localhost.

1. Run `python scripts/check_local_evm_fork.py --local-rpc-url http://127.0.0.1:8545` first.
2. Then run `python scripts/aave_readonly_discovery.py --root-address <root-address> --local-rpc-url http://127.0.0.1:8545`.
3. Discovery can be `full`, `partial`, `unavailable`, or `missing-root`.
4. You may export a safe read-only target manifest with `--export-target targets/generated/aave_v3_readonly.yaml`.
5. No transactions are sent.
6. Red drills are not executed on Aave.
7. MockArena remains separate and is not used as an Aave fallback.
8. Phase 2B is future work for mediated local fork execution.

## Phase 2A QA: fixture vs optional live local fork

Default CI is fixture-backed and proves read-only safety, resolver plumbing, safe failure behavior, and report sanitization. It does not prove that your machine has a working local fork or that a specific Aave deployment is fully decoded.

Optional manual live local fork smoke:

```bash
python scripts/manual_live_fork_smoke.py --local-rpc-url http://127.0.0.1:8545 --root-address <root-address>
```

This manual command is not run in CI. It still sends no transactions, uses no signing keys, executes no Aave Red drills, and does not enable Phase 2B. See `docs/PHASE_2A_DEPTH_AUDIT.md` and `docs/PHASE_2B_READINESS_CHECKLIST.md` before planning executable fork work.

## Phase 2B design-only status

Phase 2B is currently design-only. Fork execution is disabled by default, `EvmForkExecutionArena.execute_local_intent()` raises `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`, and no executable EVM fork Red drills are implemented.

Before any Phase 2B implementation, review `docs/PHASE_2B_FORK_EXECUTION_DESIGN.md`, `docs/PHASE_2B_FIRST_DRILL_CANDIDATE.md`, and `docs/PHASE_2B_READINESS_CHECKLIST.md`. The proposed first drill is a harmless snapshot/revert and liveness sentinel, not an exploit and not a fund-moving drill.
