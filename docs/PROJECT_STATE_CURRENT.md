# Project State Current — 2026-06-11

## Continuity warning

Do not restart the architecture.
Do not replace existing modules.
Continue from the current mainline project state.

This repository is the **DeFi Defense Simulation Lab**.
It is a defensive, isolated research framework for validating DeFi defense systems
through local Recon / Red / Blue / Evaluation workflows against a confirmed target
protocol or Protocol Twin.

It is not a public-network attack tool.
It is not a text-only scenario generator.

## Latest completed phase

Latest completed phase: **Phase 2A.6-OP — Live Review Fixture Expansion & Manual Operator Guide Validation**.

Phase 2A.6-OP adds an operator guide, manual review checklist, deterministic
safe sample bundle, sample bundle manifest review path, and current-PR review
packet. It is operator guidance and review validation only. It does not run live
discovery, does not contact public RPC, and does not grant execution permission.

Previous completed phase: **Phase 2A.6-RP — Codex PR Review Packet & Verification Gate**.
Phase 2A.6-RP adds a mandatory Codex PR review packet protocol, a local verifier,
a model review packet, and a PR template checklist.

Previous live-review phase: **Phase 2A.6-Live Review — User-provided live-local
artifact assessment**. Phase 2A.6-Live Review adds a read-only bundle review pass
for user-provided localhost artifacts and feeds safe inputs into the existing
Phase 2A.6 evidence quality review path.

Previous hardening phase: **Phase 2A.6-H1 — Source Format Integrity & Hidden
Unicode Hygiene**. Phase 2A.6-H1 verifies source/doc formatting, rejects hidden
bidirectional Unicode controls, and keeps evidence review readable in raw
repository views.

Phase 2A.6 added a read-only evidence quality review layer over the Phase 2A.5
evidence workflow. It evaluates:

- evidence completeness
- ABI/decode quality
- reserve coverage
- dependency review quality
- target manifest review quality
- Phase 2B blockers

Phase 2A.6 does not enable Phase 2B execution.

## Previous key phase

Previous key design phase: **Phase 2A.5-R — Recon / Red / Blue Extreme
Capability Reframe**.

Phase 2A.5-R established:

- External public-world behavior is forbidden.
- Internal sealed-lab equivalents must be modeled with maximum realism.
- 외부 세계에서는 금지한다.
- 내부 실험실에서는 현실과 똑같이, 오히려 더 극한적으로 구현한다.
- Red가 최강이려면 Recon은 더 최강이어야 한다.
- For Red to be world-class, Recon must be stronger than Red.

## Current supported capabilities

- MockArena executable local simulation
- Blind Blue defense
- Independent Red drills in MockArena
- Multi-mode evaluation
- TargetProtocolSpec-driven Recon
- Scorecards
- SafetyGuard and report sanitizer
- Protocol Twin scaffold
- External World Twin concepts
- EVM Fork Twin read-only path through Phase 2A.5
- Aave V3 core and reserve-aware read-only discovery
- Aave reserve metadata flowing into Recon
- Live fork evidence pack workflow
- Target manifest review
- Dependency graph review
- Phase 2B preflight review gate
- Phase 2A.5-R Recon/Red/Blue capability boundary model
- Phase 2A.6 evidence quality review model and report generation
- Phase 2A.6-H1 source format and hidden Unicode hygiene checks
- Phase 2A.6-Live Review user-provided artifact bundle assessment
- Codex PR Review Packet protocol
- Review packet verifier
- PR template review checklist
- Reviewer focus map
- Claims-to-verify review section
- Phase 2A.6 operator guide
- Phase 2A.6 manual review checklist
- deterministic safe live-review sample bundle
- sample bundle manifest review
- review packet verified for current PR

## Current unsupported capabilities

- executable EVM fork Red drills
- actual local fork transaction execution
- live fork mempool defense
- real Aave defense bot
- real public network execution
- real private key support
- real fund movement
- Haedal / Sui State Twin
- Sui / Move localnet adapter

## Permanent forbidden outside / modeled inside principle

Permanent forbidden outside the sealed lab:

- public network active probing
- public network transaction broadcast
- public RPC through Red/Blue execution
- live victim targeting
- public mempool observation for attack discovery
- real private key usage
- real fund movement
- out-of-scope contract/program exploration
- replayable exploit package generation
- raw reusable calldata / transaction bundle output
- public-network portable exploit artifacts

These are forbidden externally.
They may be modeled internally only after proper sealed-lab gates.

## Existing files/modules that must be preserved

Do not replace or rewrite these as a new framework:

- `arenas/mock_arena.py`
- `arenas/evm_fork_execution_arena.py`
- `core/safety.py`
- `core/capability_boundary.py`
- `core/containment_policy.py`
- `evidence/live_fork_evidence.py`
- `evidence/evidence_quality.py`
- `evidence/live_artifact_bundle.py`
- `recon/recon_engine.py`
- `recon/extreme_recon_model.py`
- `targets/aave_v3_readonly.py`
- `scripts/generate_live_fork_evidence_pack.py`
- `scripts/generate_dependency_graph_review.py`
- `scripts/review_target_manifest.py`
- `scripts/phase2b_preflight.py`
- `scripts/review_live_fork_evidence_quality.py`
- `scripts/review_live_artifact_bundle.py`
- `scripts/verify_codex_review_packet.py`
- `docs/SAFETY_BOUNDARY_MODEL.md`
- `docs/NO_FAKE_SCENARIO_STANDARD.md`
- `docs/RECON_TO_RED_DRILL_PIPELINE.md`
- `docs/RECON_CAPABILITY_BOUNDARY.md`
- `docs/RED_TEAM_CAPABILITY_BOUNDARY.md`
- `docs/BLUE_TEAM_CAPABILITY_BOUNDARY.md`
- `docs/CODEX_PR_REVIEW_PROTOCOL.md`
- `docs/reviews/REVIEW_PACKET_TEMPLATE.md`
- `docs/PHASE_2A6_OPERATOR_GUIDE.md`
- `docs/PHASE_2A6_MANUAL_REVIEW_CHECKLIST.md`

## Next recommended step

Recommended next step: **Phase 2A.6 live-review fixture expansion and manual
operator guide validation**.

Future work may add more deterministic safe sample bundles and clearer manual
operator handoff examples. Do not begin executable fork drills until a separate
explicit Phase 2B PR opens sealed local execution with snapshot/revert, manifest
scope, sanitized evidence, and SafetyGuard enforcement.

## Exact validation commands

```bash
pytest -q
python main.py
python scripts/verify_mvp.py
python scripts/review_live_fork_evidence_quality.py --fixture-demo --output /tmp/phase2a6_evidence_quality_report.md
python scripts/review_live_artifact_bundle.py --fixture-demo --output /tmp/live_artifact_bundle_review.md
python scripts/review_live_artifact_bundle.py \
  --artifact-dir docs/examples/phase2a6_live_bundle \
  --output /tmp/phase2a6_example_bundle_review.md
python scripts/review_live_artifact_bundle.py \
  --bundle-manifest docs/examples/phase2a6_live_bundle/live_artifact_bundle.yaml \
  --output /tmp/phase2a6_example_bundle_manifest_review.md
python -m py_compile evidence/evidence_quality.py evidence/live_artifact_bundle.py \
  scripts/review_live_fork_evidence_quality.py scripts/review_live_artifact_bundle.py
python -m py_compile scripts/verify_codex_review_packet.py
python scripts/verify_codex_review_packet.py --packet docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md
python scripts/verify_codex_review_packet.py --packet docs/reviews/PHASE_2A6_OP_REVIEW_PACKET.md
git status --short
```

## Final warning

Do not restart architecture.
Do not replace existing modules.
Do not bypass SafetyGuard.
Do not enable Phase 2B.
Continue from current mainline state.
