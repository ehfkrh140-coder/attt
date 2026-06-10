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
