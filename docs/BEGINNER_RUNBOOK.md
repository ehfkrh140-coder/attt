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

## Phase 2A.1: how local fork read-only discovery works

Phase 2A.1 lets the project read from a local EVM fork using safe JSON-RPC reads. You must start the fork yourself with your own local tooling. The simulation bots only connect to `http://127.0.0.1:8545` or `http://localhost:8545`.

Try Aave V3 read-only discovery like this after your local fork is running:

```bash
python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum --root-address <root-address> --local-rpc-url http://127.0.0.1:8545
```

If no local fork is running, the command should print `LOCAL_FORK_UNAVAILABLE`. That is a safe failure. Phase 2A.1 does not send transactions, does not use private keys, does not execute Aave Red drills, and does not silently switch to MockArena.

## Live local fork read-only smoke

Use this section when you want to check a local Anvil or Hardhat-style fork that you started yourself. Start your local fork with your own local tooling and upstream provider outside this project. This project only connects to localhost.

1. Check the local fork:

```bash
python scripts/check_local_evm_fork.py --local-rpc-url http://127.0.0.1:8545
```

2. If you have an Aave V3 PoolAddressesProvider/root address, run read-only discovery:

```bash
python scripts/aave_readonly_discovery.py --root-address <root-address> --local-rpc-url http://127.0.0.1:8545
```

If the fork is not running, `LOCAL_FORK_UNAVAILABLE` is safe and expected. The scripts do not send transactions, do not use signing keys, do not run executable Aave Red drills, and do not switch to MockArena as a fallback.

## Phase 2A Read-only Local Fork Workflow

Use Phase 2A when you want to inspect a real EVM protocol through a local fork without running attacks or defenses on that fork.

1. Start a local fork yourself with your own local tooling. This project only connects to localhost.
2. Check the fork first: `python scripts/check_local_evm_fork.py --local-rpc-url http://127.0.0.1:8545`.
3. Run Aave V3 read-only discovery with a root address: `python scripts/aave_readonly_discovery.py --root-address <root-address> --local-rpc-url http://127.0.0.1:8545`.
4. Read-only discovery can be `full`, `partial`, `unavailable`, or `missing-root`.
5. Add `--export-target targets/generated/aave_v3_readonly.yaml` if you want a safe unconfirmed target manifest.
6. No transactions are sent.
7. Red drills are not executed on Aave.
8. MockArena remains separate and is not used as an Aave fallback.
9. Phase 2B is future work for mediated local fork execution.

## Phase 2A QA: fixture tests vs manual live fork

The GitHub Actions tests are fixture-backed. That means they prove the read-only code path and safety checks, but they do not prove your own local fork is running correctly.

If you have started a local fork yourself, you may run the optional manual smoke:

```bash
python scripts/manual_live_fork_smoke.py --local-rpc-url http://127.0.0.1:8545 --root-address <root-address>
```

This optional command is not run in CI. It sends no transactions, uses no signing keys, and does not execute Red drills on Aave. Phase 2B is future work and requires the checklist in `docs/PHASE_2B_READINESS_CHECKLIST.md`.
