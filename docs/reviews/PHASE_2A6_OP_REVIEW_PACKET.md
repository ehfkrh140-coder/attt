# Codex PR Review Packet — Phase 2A.6-OP

## 1. Review Packet Header

- Phase: Phase 2A.6-OP — Live Review Fixture Expansion & Manual Operator Guide Validation
- PR title: Phase 2A.6-OP: Add operator guide and safe sample bundle
- Branch: codex/phase-2a6-op-operator-guide
- Commit: to be set by repository commit after implementation
- Date: 2026-06-11
- Scope: narrow operator guide, manual checklist, deterministic samples, OP review packet, and tests
- Execution status: review-only; no execution permission granted

## 2. Continuity Summary

- Latest completed phase before PR: Phase 2A.6-RP — Codex PR Review Packet & Verification Gate.

- Superseded PR note: broad PR #31 is superseded by this narrow Phase 2A.6-OP review packet.
  This packet is intended for an open PR that remains unmerged until external design review and explicit merge approval.
- Previous live-review phase: Phase 2A.6-Live Review — User-provided live-local artifact assessment.
- Previous hardening phase: Phase 2A.6-H1 — Source Format Integrity & Hidden Unicode Hygiene.
- Previous key design phase: Phase 2A.5-R — Recon / Red / Blue Extreme Capability Reframe.
- Preserved modules:
  - `arenas/mock_arena.py`
  - `arenas/evm_fork_execution_arena.py`
  - `core/safety.py`
  - `core/capability_boundary.py`
  - `core/containment_policy.py`
  - `evidence/evidence_quality.py`
  - `evidence/live_artifact_bundle.py`
  - `scripts/review_live_fork_evidence_quality.py`
  - `scripts/review_live_artifact_bundle.py`
  - `scripts/verify_codex_review_packet.py`
- Not replaced modules: MockArena, Recon, Evidence, Aave read-only discovery, Phase 2B preflight,
  SafetyGuard, Phase 2A.5-R capability models, Phase 2A.6 evidence review, Phase 2A.6-H1 hygiene
  checks, Phase 2A.6-Live artifact bundle review, and Phase 2A.6-RP review packet governance.
- Current unsupported capabilities remain unchanged:
  - executable EVM fork Red drills
  - actual local fork transaction execution
  - live fork mempool defense
  - real Aave defense bot
  - real public network execution
  - real secret signing material support
  - real fund movement
  - Haedal / Sui State Twin
  - Sui / Move localnet adapter

## 3. Change Map

- Docs:
  - `docs/PHASE_2A6_OPERATOR_GUIDE.md`
  - `docs/PHASE_2A6_MANUAL_REVIEW_CHECKLIST.md`
  - `docs/reviews/PHASE_2A6_OP_REVIEW_PACKET.md`
  - `docs/PROJECT_STATE_CURRENT.md`
  - `docs/CAPABILITY_STATUS.md`
  - `docs/PHASE_2B_READINESS_CHECKLIST.md`
- Code:
  - `evidence/live_artifact_bundle.py`
- Scripts: none replaced; existing `scripts/review_live_artifact_bundle.py` remains the review entrypoint.
- Tests:
  - `tests/test_phase2a6_operator_guide.py`
- CI / GitHub templates:
  - `.github/workflows/test.yml`
- Generated safe reports: none committed beyond deterministic sample artifacts.
- Sample artifacts:
  - `docs/examples/phase2a6_live_bundle/`

## 4. Reviewer Focus Map

- `docs/PHASE_2A6_OPERATOR_GUIDE.md` — operator workflow and safety assumptions.
- `docs/PHASE_2A6_MANUAL_REVIEW_CHECKLIST.md` — reviewer sign-off checklist.
- `docs/examples/phase2a6_live_bundle/` — deterministic safe sample bundle.
- `evidence/live_artifact_bundle.py` — operator next-action summary in generated review markdown.
- `tests/test_phase2a6_operator_guide.py` — sample bundle, guide, sanitizer, and gate coverage.
- `arenas/evm_fork_execution_arena.py` — source of truth for disabled Phase 2B execution.

## 5. Safety Boundary Confirmation

- No transaction sending: confirmed.
- No secret signing material: confirmed.
- No public RPC Red/Blue execution: confirmed.
- No live victim targeting: confirmed.
- No public mempool observation: confirmed.
- No reusable invocation output: confirmed.
- No bundled transaction output: confirmed.
- No replayable exploit package: confirmed.
- No Phase 2B enablement: confirmed.

## 6. Phase Gate Confirmation

- Current phase: Phase 2A.6-OP — Live Review Fixture Expansion & Manual Operator Guide Validation.
- Phase 2B status: disabled.
- Execution permission granted: no.
- `EvmForkExecutionArena.execute_local_intent()` must still raise
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.
- This PR adds operator guidance and deterministic samples only.

## 7. Validation Evidence

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
python -m py_compile scripts/verify_codex_review_packet.py evidence/evidence_quality.py \
  evidence/live_artifact_bundle.py scripts/review_live_fork_evidence_quality.py scripts/review_live_artifact_bundle.py
python scripts/verify_codex_review_packet.py --packet docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md
python scripts/verify_codex_review_packet.py --packet docs/reviews/PHASE_2A6_OP_REVIEW_PACKET.md
git status --short
```

## 8. Claims to Independently Verify

- GitHub PR merged status must be checked by reviewer.
- GitHub checks status must be checked by reviewer.
- `EvmForkExecutionArena` code must be inspected by reviewer.
- `docs/PROJECT_STATE_CURRENT.md` phase must be inspected by reviewer.
- `docs/examples/phase2a6_live_bundle/` sample files must be inspected by reviewer.
- Review packet should guide review, not replace review.
- GitHub files, tests, CI, and code remain source of truth.

## 9. Remaining Gaps

- This PR adds operator guidance and deterministic samples only.
- No real user-provided live-local evidence has been reviewed unless the user supplies it.
- It does not begin Phase 2B.
- It does not prove live local fork ABI compatibility.
- It does not add executable fork drills.

## 10. Next Recommended PR

- Phase 2A.6 user-supplied artifact dry-run review, if a reviewer provides sanitized localhost artifacts.
