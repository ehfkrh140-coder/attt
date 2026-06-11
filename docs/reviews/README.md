# Codex Review Packets

This directory stores structured Codex PR review packets.

A review packet is a falsifiable review guide. It does not replace independent
review, CI logs, GitHub diff inspection, or direct code inspection.

## How reviewers should use packets

1. Open the packet for the PR phase.
2. Read the reviewer focus map first.
3. Inspect the referenced files in GitHub.
4. Confirm safety and phase gates from source files, not only from the packet.
5. Compare validation commands with CI logs.
6. Check remaining gaps and next PR recommendation.

## Required files

- `REVIEW_PACKET_TEMPLATE.md` — copy this for future Codex PRs.
- `PHASE_2A6_RP_REVIEW_PACKET.md` — model packet for Phase 2A.6-RP.

## Verification

Run:

```bash
python scripts/verify_codex_review_packet.py --packet docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md
```

The verifier checks required sections, safety claims, hidden bidirectional
Unicode controls, readability, and forbidden execution-ready claims.
