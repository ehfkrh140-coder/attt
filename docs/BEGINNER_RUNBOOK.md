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
