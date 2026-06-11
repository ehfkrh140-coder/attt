# Codex PR Review Packet Protocol

## Purpose

Every future Codex development PR must leave a structured review packet. The
packet is a falsifiable guide for human and GPT-assisted reviewers. It reduces
manual copy/paste reporting, but it does not replace independent review.

Codex review packets reduce reviewer burden but do not replace independent
review. GitHub files, tests, CI, and code remain the source of truth.

## Why this protocol exists

The DeFi Defense Simulation Lab depends on continuity, safety gates, and honest
phase boundaries. A free-form completion summary is not enough because reviewers
must quickly answer:

1. What changed?
2. Why was it changed?
3. Which existing modules were preserved?
4. Which safety boundaries remain intact?
5. What tests prove the claim?
6. What claims still need independent GitHub or CI verification?
7. What changed files should the reviewer inspect first?
8. What is the next recommended PR?
9. What remains blocked?
10. Did this PR accidentally enable Phase 2B or any forbidden capability?

## Review packet is not proof

A review packet is Codex self-report plus a reviewer map. It is useful only when
it is falsifiable against repository files, tests, CI logs, and direct code
inspection.

Reviewers should treat the packet as a checklist, not as evidence by itself.

## Required packet location

Each Codex PR should add or update a packet under:

```text
docs/reviews/
```

For example:

```text
docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md
```

## Required sections

Every packet must include these visible Markdown headings:

1. `## 1. Review Packet Header`
2. `## 2. Continuity Summary`
3. `## 3. Change Map`
4. `## 4. Reviewer Focus Map`
5. `## 5. Safety Boundary Confirmation`
6. `## 6. Phase Gate Confirmation`
7. `## 7. Validation Evidence`
8. `## 8. Claims to Independently Verify`
9. `## 9. Remaining Gaps`
10. `## 10. Next Recommended PR`

## Required header fields

The header must state:

- phase
- PR title
- branch
- commit
- date
- scope
- execution status

## Required safety assertions

The safety section must explicitly confirm:

- no transaction sending
- no secret signing material
- no public RPC Red/Blue execution
- no live victim targeting
- no public mempool observation
- no reusable invocation output
- no bundled transaction output
- no replayable exploit package
- no Phase 2B enablement

## Required phase gate confirmation

The phase gate section must state:

- current phase
- whether the PR changes Phase 2B status
- whether execution permission is granted
- whether `EvmForkExecutionArena.execute_local_intent()` remains blocked

For Phase 2A review PRs, the expected gate language is:

- Phase 2B status: disabled
- Execution permission granted: no
- `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`

## Required validation commands

The validation evidence section must list exact commands run. For this project,
the common baseline is:

```bash
pytest -q
python main.py
python scripts/verify_mvp.py
python scripts/review_live_fork_evidence_quality.py --fixture-demo --output /tmp/phase2a6_evidence_quality_report.md
python scripts/review_live_artifact_bundle.py --fixture-demo --output /tmp/live_artifact_bundle_review.md
python -m py_compile evidence/evidence_quality.py evidence/live_artifact_bundle.py \
  scripts/review_live_fork_evidence_quality.py scripts/review_live_artifact_bundle.py
python scripts/verify_codex_review_packet.py --packet docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md
git status --short
```

A PR may add more commands, but it must not remove relevant safety checks.

## Required claims-to-verify section

The packet must ask reviewers to verify at least:

- GitHub PR merged status.
- GitHub checks status.
- `EvmForkExecutionArena` blocked execution path.
- `docs/PROJECT_STATE_CURRENT.md` phase and continuity checkpoint.
- That the review packet guides review but does not replace review.

## Required reviewer focus map

The packet must list changed files by review priority and explain why each file
matters. A reviewer should be able to inspect the focus map first and quickly
choose the highest-risk files.

## Required remaining gaps

The packet must honestly list what the PR does not prove. For review/governance
PRs, this usually includes:

- no real user-provided live-local artifact was reviewed,
- no executable fork drills were added,
- Phase 2B did not begin,
- live local fork ABI compatibility was not proven.

## Required next PR recommendation

The final section must recommend the next bounded PR. The recommendation should
not skip phase gates or imply execution approval.

## Verification gate

Run the verifier locally:

```bash
python scripts/verify_codex_review_packet.py --packet docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md
```

GitHub PR event body verification is available for CI environments:

```bash
python scripts/verify_codex_review_packet.py --github-event "$GITHUB_EVENT_PATH"
```

Event mode reads the PR body from the local event payload. It does not call the
GitHub API, does not require secrets, and does not require network access.
