# Codex PR Review Packet — <Phase / Short Title>

## 1. Review Packet Header

- Phase: `<phase>`
- PR title: `<title>`
- Branch: `<branch>`
- Commit: `<commit>`
- Date: `<YYYY-MM-DD>`
- Scope: `<docs/code/scripts/tests/governance>`
- Execution status: review-only / local-only / disabled

## 2. Continuity Summary

- Latest completed phase before PR: `<phase>`
- Preserved modules: `<list>`
- Not replaced modules: `<list>`
- Current unsupported capabilities: `<list>`

## 3. Change Map

- Docs: `<files>`
- Code: `<files>`
- Scripts: `<files>`
- Tests: `<files>`
- CI / GitHub templates: `<files>`
- Generated safe reports: `<files>`

## 4. Reviewer Focus Map

- `<file>` — `<why reviewer should inspect it>`

## 5. Safety Boundary Confirmation

- No transaction sending: confirmed
- No secret signing material: confirmed
- No public RPC Red/Blue execution: confirmed
- No live victim targeting: confirmed
- No public mempool observation: confirmed
- No reusable invocation output: confirmed
- No bundled transaction output: confirmed
- No replayable exploit package: confirmed
- No Phase 2B enablement: confirmed

## 6. Phase Gate Confirmation

- Current phase: `<phase>`
- Phase 2B status: disabled
- Execution permission granted: no
- `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`

## 7. Validation Evidence

```bash
pytest -q
python main.py
python scripts/verify_mvp.py
python scripts/review_live_fork_evidence_quality.py --fixture-demo --output /tmp/phase2a6_evidence_quality_report.md
python scripts/review_live_artifact_bundle.py --fixture-demo --output /tmp/live_artifact_bundle_review.md
python -m py_compile evidence/evidence_quality.py evidence/live_artifact_bundle.py \
  scripts/review_live_fork_evidence_quality.py scripts/review_live_artifact_bundle.py
python scripts/verify_codex_review_packet.py --packet docs/reviews/<packet>.md
git status --short
```

## 8. Claims to Independently Verify

- GitHub PR merged status must be checked by reviewer.
- GitHub checks status must be checked by reviewer.
- `EvmForkExecutionArena` code must be inspected by reviewer.
- `docs/PROJECT_STATE_CURRENT.md` phase must be inspected by reviewer.
- Review packet should guide review, not replace review.

## 9. Remaining Gaps

- `<honest gap>`

## 10. Next Recommended PR

- `<bounded next PR>`
