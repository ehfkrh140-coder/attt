# Beginner Runbook

This runbook explains how to use the current MockArena MVP safely.

## What this project does

DeFi Defense Simulation Lab is a defensive research project. It runs executable Red Team drills inside a fully isolated local mock arena, lets the Blue Team defender see only blind safe features, and evaluates the result with local state changes, state diffs, and invariant checks.

The current MVP is useful for learning the full flow:

```text
TargetProtocolSpec -> Recon -> Red local drill -> Blind Blue defense -> Evaluation scorecard
```

## What this project does not do

This MVP does not run against real protocols or real funds. It does not send transactions to public networks. It does not use real private keys. It does not implement the real EVM fork adapter or the real Sui localnet adapter yet.

## Install and run tests

From the repository root, run:

```bash
pip install -e ".[test]"
pytest -q
```

A passing test run means the local mock MVP, safety checks, blind-observable checks, scoring checks, and regression suite are working in your environment.

## Run the demo

Run:

```bash
python main.py
```

The demo prints a beginner-readable summary. It does not print raw transaction payloads, keys, or reusable attack details.

## How to read the output

The demo prints five top-level scores:

- Recon score: how well Recon builds target-specific surfaces, dependency paths, invariants, and drill recommendations.
- Red drill score: how diverse and executable the local drills are in the MockArena MVP.
- Blue defense score: how well Blue blocks or limits visible and hidden local drill pressure.
- Safety score: whether containment checks block unsafe execution paths and unsafe reports.
- Evaluation quality score: whether evaluation uses state diffs, invariants, multiple ordering modes, and honest damage recording.

The demo also prints the number of regression cases and the ordering modes tested.

## What MockArena means

MockArena is a local-only simulated protocol arena. It changes local Python state to represent protocol conditions such as oracle drift, liquidity pressure, vault accounting pressure, and circuit-breaker pauses. MockArena is the supported executable MVP runtime.

## Why EVM and Sui are gated

EVM fork and Sui localnet files are placeholders until real isolated adapters exist. They are intentionally marked as gated so the project does not claim public-chain or real-adapter execution before it is safely implemented and tested.

## GitHub Actions

After pushing a branch or opening a pull request, check the GitHub **Actions** tab. The `tests` workflow should run:

```bash
pytest -q
python main.py
```

If the workflow is green, GitHub confirmed the same basic checks that you can run locally.

## What to send back to a reviewer after each Codex task

Send:

1. A short summary of what changed.
2. The exact commands you ran, especially `pytest -q` and `python main.py`.
3. Whether the GitHub Actions workflow passed.
4. Any honest limitations that remain, such as EVM/Sui adapters still being gated.

## Protocol Twin vs External World Twin

An EVM Fork Twin copies on-chain state into a local EVM fork. That is useful, but a fork alone does not reproduce live mempool behavior, keeper timing, future oracle updates, offchain APIs, bridge remote-chain state, frontend behavior, bot timing, or congestion.

The External World Twin locally emulates those missing pieces. It can add private orderflow, stale oracle windows, delayed keepers, local liquidity shocks, bridge delay stubs, offchain data stubs, withdrawal bursts, gas priority pressure, and timestamp jumps.

This is best described as a fork twin + emulated external environment. The Twin Fidelity Score explains which parts were copied, which parts were emulated, which parts are unsupported, and how much confidence to place in the result.

You do not need to manually design scenarios. For supported modes, Recon builds risk hypotheses and the auto runner selects Red drills automatically.

## Protocol choices

- `mock_lending`: runs the full MockArena learning and regression simulation.
- `aave_v3`: uses the EVM Fork Twin path. If a root address is missing, the CLI reports `MISSING_PROTOCOL_ROOT_ADDRESS`. If executable EVM support is not ready, it reports gated/read-only status instead of silently using a mock.
- `haedal`: reports `UNSUPPORTED_PROTOCOL_TWIN` until the Sui state twin adapter exists.

## Protocol Twin commands

```bash
python scripts/run_protocol_twin.py --protocol mock_lending
python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum --fork-block latest
python scripts/create_protocol_twin.py --protocol aave_v3 --network ethereum --root-address <root-address> --fork-block latest
python scripts/run_protocol_twin.py --protocol haedal
```

`mock_lending` is the safe learning and regression path. `aave_v3` uses the EVM Fork Twin onboarding path and reports missing root or gated execution status when needed. `haedal` reports unsupported status until a Sui state twin adapter exists.

## How do I know it works?

A beginner can verify the v0.1.0 MVP by checking:

1. GitHub Actions `tests` workflow is green.
2. `python main.py` prints the five score summary.
3. `python scripts/verify_mvp.py` prints `Overall: PASS`.
4. `docs/CAPABILITY_STATUS.md` honestly says what is supported, partial/gated, and unsupported.
5. `python scripts/run_protocol_twin.py --protocol mock_lending` runs the MockArena simulation.
6. `python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum` reports missing-root or gated/read-only status safely.
7. `python scripts/run_protocol_twin.py --protocol haedal` reports unsupported Sui adapter status safely.

## Phase 2A read-only EVM Fork Twin

Phase 2A is a read-only onboarding step for EVM protocols. For Aave V3, you provide a local fork setting and a root address, and the resolver can discover PoolAddressesProvider, Pool, PoolConfigurator, PriceOracle, and ACLManager through safe read-only calls.

Read-only means no transactions, no approvals, no transfers, no private keys, no executable fork Red drills, and no public mempool. The output lists planned Red drill recommendations as gated rather than executed.
