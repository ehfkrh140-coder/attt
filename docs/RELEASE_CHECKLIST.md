# v0.1.0 Release Checklist

Use this checklist before treating the MockArena MVP as release-ready.

- [ ] `pytest -q` passes.
- [ ] `python main.py` runs.
- [ ] `python scripts/run_protocol_twin.py --protocol mock_lending` runs.
- [ ] `python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum` handles missing-root or gated status safely.
- [ ] `python scripts/run_protocol_twin.py --protocol haedal` returns unsupported Sui adapter status safely.
- [ ] `python scripts/verify_mvp.py` runs.
- [ ] GitHub Actions `tests` workflow is green.
- [ ] README quick start works.
- [ ] Beginner runbook exists.
- [ ] Capability status exists.
- [ ] MockArena-only executable status is clear.
- [ ] EVM Fork Twin is read-only/gated, not executable.
- [ ] Sui State Twin is unsupported/gated.
- [ ] Real Aave adapter is not implemented.
- [ ] Real Haedal adapter is not implemented.
- [ ] No public network transaction broadcast exists.
- [ ] No real private keys exist.
- [ ] No raw reusable calldata appears in reports.
- [ ] No unsafe artifacts appear in CLI output.
- [ ] Protocol Twin / External World Twin limitations are documented.
- [ ] Twin Fidelity Score appears in beginner-facing output.
- [ ] Version marker exists and matches `pyproject.toml`.

## Release scope

v0.1.0 is a MockArena MVP baseline. It supports local executable mock drills, Protocol Twin onboarding scaffold, External World Twin local emulation, scorecards, Twin Fidelity Score, safe summaries, tests, and CI visibility.

It does not implement executable EVM fork Red drills, a real Aave adapter, a Sui State Twin adapter, or a real Haedal adapter.

## Phase 2A read-only checks

- [ ] EVM read-only client accepts local fork RPC settings only.
- [ ] EVM read-only client exposes no send transaction methods.
- [ ] Aave V3 root-address resolver builds a partial read-only `TargetProtocolSpec`.
- [ ] Aave V3 read-only CLI output says executable drills did not run.
- [ ] Aave V3 read-only CLI output says execution is gated.
- [ ] Phase 2A smoke check appears in `python scripts/verify_mvp.py` output.
