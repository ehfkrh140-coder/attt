# Phase 2A.6 Manual Review Checklist

Use this checklist when reviewing a live-local artifact bundle or deterministic
sample bundle.

## Artifact source classification

- [ ] Evidence source is classified as fixture-backed, live-local, missing, unsafe, or unknown.
- [ ] Fixture-backed evidence is not treated as execution-ready.
- [ ] Live-local evidence is treated as review-ready only.

## Localhost-only verification

- [ ] Artifacts reference localhost, loopback, or mock endpoint labels only.
- [ ] No public RPC Red/Blue execution is present.
- [ ] No transaction sending is present.

## Required artifact presence

- [ ] Evidence pack is present.
- [ ] Target manifest is present.
- [ ] Dependency graph review is present.
- [ ] Manual live smoke result is present or explicitly missing as a finding.
- [ ] Phase 2B preflight output is present or explicitly missing as a finding.

## Evidence quality review

- [ ] ABI/decode triage findings are reviewed.
- [ ] Reserve coverage findings are reviewed.
- [ ] Manifest scope findings are reviewed.
- [ ] Dependency graph findings are reviewed.
- [ ] Phase 2B blockers are reviewed.

## Sanitized report review

- [ ] Unsafe content scan completed.
- [ ] Generated reports do not print unsafe artifact contents.
- [ ] Reports clearly state execution permission is not granted.
- [ ] Reports clearly state Phase 2B remains disabled.

## Reviewer sign-off

- [ ] I inspected the artifact directory or manifest.
- [ ] I inspected the bundle review output.
- [ ] I inspected the evidence quality output when available.
- [ ] I confirm review success is not execution permission.
- [ ] I confirm executable fork drills remain blocked.
