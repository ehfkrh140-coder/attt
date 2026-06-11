from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

BIDI_CONTROL_CODEPOINTS = {
    0x202A,
    0x202B,
    0x202C,
    0x202D,
    0x202E,
    0x2066,
    0x2067,
    0x2068,
    0x2069,
}

REQUIRED_SECTIONS = (
    "## 1. Review Packet Header",
    "## 2. Continuity Summary",
    "## 3. Change Map",
    "## 4. Reviewer Focus Map",
    "## 5. Safety Boundary Confirmation",
    "## 6. Phase Gate Confirmation",
    "## 7. Validation Evidence",
    "## 8. Claims to Independently Verify",
    "## 9. Remaining Gaps",
    "## 10. Next Recommended PR",
)

REQUIRED_PHRASES = (
    "Phase:",
    "PR title:",
    "Branch:",
    "Commit:",
    "Date:",
    "Scope:",
    "Execution status:",
    "Execution permission granted: no",
    "Phase 2B status: disabled",
    "UNSUPPORTED_EXECUTABLE_FORK_DRILLS",
    "pytest -q",
    "python main.py",
    "python scripts/verify_mvp.py",
    "Reviewer Focus Map",
    "Claims to Independently Verify",
    "Review packet should guide review, not replace review",
)

FORBIDDEN_PATTERNS = (
    (re.compile(r"(?<!NOT_)\bEXECUTION_READY\b"), "standalone execution-ready verdict"),
    (re.compile(r"execution\s+permission\s+granted\s*:\s*yes", re.IGNORECASE), "execution permission claim"),
    (re.compile(r"phase\s*2b\s+status\s*:\s*enabled", re.IGNORECASE), "Phase 2B enabled claim"),
    (re.compile(r"raw_calldata", re.IGNORECASE), "unsafe invocation artifact token"),
    (re.compile(r"raw\s+calldata", re.IGNORECASE), "unsafe invocation artifact phrase"),
    (re.compile(r"calldata\s*:", re.IGNORECASE), "unsafe invocation field"),
    (re.compile(r"transaction\s+bundle", re.IGNORECASE), "unsafe bundled execution text"),
    (re.compile(r"private_key", re.IGNORECASE), "unsafe signing material token"),
    (re.compile(r"private\s+key\s*:", re.IGNORECASE), "unsafe signing material field"),
    (re.compile(r"seed\s+phrase", re.IGNORECASE), "unsafe recovery material token"),
    (re.compile(r"https?://(?!localhost(?::|/|$)|127\.0\.0\.1(?::|/|$)|\[::1\](?::|/|$))", re.IGNORECASE), "upstream endpoint URL"),
    (re.compile(r"\b(infura|alchemy|quicknode|ankr|blastapi|publicnode)\b", re.IGNORECASE), "upstream endpoint provider"),
    (re.compile(r"exploit\s+artifact\s*:\s*present", re.IGNORECASE), "public-network exploit artifact claim"),
    (re.compile(r"replayable\s+exploit\s+payload", re.IGNORECASE), "replayable exploit payload"),
    (re.compile(r"0x[a-fA-F0-9]{16,}"), "long reusable hex-looking payload"),
)


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    findings: tuple[str, ...]

    def to_text(self) -> str:
        if self.ok:
            return "Codex review packet verification: PASS"
        lines = ["Codex review packet verification: FAIL"]
        lines.extend(f"- {finding}" for finding in self.findings)
        return "\n".join(lines)


def verify_packet_text(text: str, *, source_label: str = "packet") -> VerificationResult:
    findings: list[str] = []
    lines = text.splitlines()

    if len(lines) < 40:
        findings.append(f"{source_label}: packet is too short or single-line-like")
    if len(lines) <= 1 and len(text) > 0:
        findings.append(f"{source_label}: packet is a single-line blob")
    long_lines = [index + 1 for index, line in enumerate(lines) if len(line) > 160]
    if long_lines:
        findings.append(f"{source_label}: lines exceed 160 characters: {long_lines[:5]}")

    bidi = [
        (line_number, hex(ord(ch)))
        for line_number, line in enumerate(lines, start=1)
        for ch in line
        if ord(ch) in BIDI_CONTROL_CODEPOINTS
    ]
    if bidi:
        findings.append(f"{source_label}: hidden bidirectional Unicode controls found: {bidi[:5]}")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            findings.append(f"{source_label}: missing required section {section!r}")

    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            findings.append(f"{source_label}: missing required phrase {phrase!r}")

    for pattern, reason in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            findings.append(f"{source_label}: forbidden content detected ({reason})")

    return VerificationResult(ok=not findings, findings=tuple(findings))


def verify_packet_file(path: str | Path) -> VerificationResult:
    packet_path = Path(path)
    if not packet_path.exists():
        return VerificationResult(False, (f"packet file not found: {packet_path}",))
    try:
        text = packet_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return VerificationResult(False, (f"packet is not valid UTF-8: {packet_path}",))
    return verify_packet_text(text, source_label=str(packet_path))


def packet_text_from_github_event(path: str | Path) -> tuple[str | None, str | None]:
    event_path = Path(path)
    if not event_path.exists():
        return None, f"GitHub event file not found: {event_path}"
    try:
        payload = json.loads(event_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, f"GitHub event file is not readable JSON: {exc}"

    pull_request = payload.get("pull_request") if isinstance(payload, dict) else None
    if isinstance(pull_request, dict) and isinstance(pull_request.get("body"), str):
        return pull_request["body"], None
    issue = payload.get("issue") if isinstance(payload, dict) else None
    if isinstance(issue, dict) and isinstance(issue.get("body"), str):
        return issue["body"], None
    return None, "GitHub event payload does not contain a PR or issue body"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify a Codex PR review packet.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--packet", help="Path to a local review packet markdown file.")
    mode.add_argument("--github-event", help="Path to a GitHub event JSON payload.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.packet:
        result = verify_packet_file(args.packet)
    else:
        text, error = packet_text_from_github_event(args.github_event)
        if error:
            result = VerificationResult(False, (error,))
        else:
            assert text is not None
            result = verify_packet_text(text, source_label="github-event-body")
    print(result.to_text())
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
