# DeFi Defense Simulation Lab

A defensive research framework for validating DeFi controls with executable, isolated local drills.

The lab is **not** a public-network attack tool and is **not** a text-only scenario generator. The MVP runs in a mock/local arena, changes local state, lets Blue observe only blind safe features, and evaluates results with snapshots, state diffs, invariants, and impact assertions.

## Flow

```text
TargetProtocolSpec
→ Recon Intelligence
→ RiskHypothesis / InvariantSpec
→ Executable Local Red Drill
→ Blind Blue Defense
→ State-Diff / Invariant Evaluation
```

## Safety boundary

- Bots may connect only to localhost/127.0.0.1 execution paths.
- Executable drills require `scope_confirmed=true` and in-scope targets.
- Red and Blue execute transactions only through Arena abstractions.
- Reports store safe labels, never raw reusable exploit calldata.
