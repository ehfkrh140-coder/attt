from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from core.errors import SafetyGuardError
from core.safety import SafetyGuard
from evidence.evidence_quality import EvidenceQualityReport, review_evidence_quality


class LiveArtifactKind(str, Enum):
    LIVE_FORK_CHECK = "live_fork_check"
    AAVE_READONLY_DISCOVERY = "aave_readonly_discovery"
    EVIDENCE_PACK = "evidence_pack"
    TARGET_MANIFEST = "target_manifest"
    DEPENDENCY_GRAPH_REVIEW = "dependency_graph_review"
    TARGET_MANIFEST_REVIEW = "target_manifest_review"
    MANUAL_LIVE_SMOKE = "manual_live_smoke"
    PHASE2B_PREFLIGHT = "phase2b_preflight"
    EVIDENCE_QUALITY_REPORT = "evidence_quality_report"


class LiveArtifactStatus(str, Enum):
    MISSING = "missing"
    PRESENT = "present"
    MALFORMED = "malformed"
    UNSAFE = "unsafe"
    FIXTURE_BACKED = "fixture-backed"
    LIVE_LOCAL = "live-local"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class LiveArtifactBundleFinding:
    kind: LiveArtifactKind
    path_label: str
    status: LiveArtifactStatus
    severity: str
    note: str


@dataclass(frozen=True)
class LiveArtifactBundle:
    artifacts: dict[LiveArtifactKind, Path]
    source: str


@dataclass(frozen=True)
class LiveArtifactBundleReview:
    source: str
    findings: tuple[LiveArtifactBundleFinding, ...]
    evidence_quality_report: EvidenceQualityReport | None = None

    @property
    def execution_permission_granted(self) -> bool:
        return False

    @property
    def phase2b_enabled(self) -> bool:
        return False

    def finding_for(self, kind: LiveArtifactKind) -> LiveArtifactBundleFinding | None:
        for finding in self.findings:
            if finding.kind == kind:
                return finding
        return None

    def to_markdown(self) -> str:
        lines = [
            "# Live Artifact Bundle Review",
            "",
            "## 1. Summary",
            "- Phase: Phase 2A.6-Live Review — User-provided live-local artifact assessment",
            f"- Bundle source: {self.source}",
            "- Execution permission granted: no",
            "- Phase 2B execution enabled: no",
            "- Review mode: read-only artifact inspection",
            "- Live-local review-ready means reviewable evidence only, never execution approval.",
            "",
            "## 2. Artifact classification",
            *self._finding_lines(),
            "",
            "## 3. Evidence quality integration",
            *self._evidence_quality_lines(),
            "",
            "## 4. Safety and sanitizer confirmation",
            "- Artifact contents embedded in this report: no",
            "- Unsafe artifact content printed: no",
            "- Public-network side effects: forbidden",
            "- Transactions sent by this review: no",
            "- Live discovery run by this review: no",
            "- Public RPC contacted by this review: no",
            "- Secret signing material included: absent",
            "- Reusable invocation artifacts included: absent",
            "- Bundled execution artifacts included: absent",
            "- Portable attack artifacts included: absent",
            "",
            "## 5. Final review note",
            "- This bundle review can improve evidence readiness only.",
            "- It cannot approve Phase 2B execution.",
        ]
        markdown = "\n".join(lines) + "\n"
        SafetyGuard().assert_safe_report(markdown)
        return markdown

    def _finding_lines(self) -> list[str]:
        if not self.findings:
            return ["- none"]
        return [
            f"- {finding.kind.value}: {finding.status.value} ({finding.severity}) — "
            f"{finding.path_label}; {finding.note}"
            for finding in self.findings
        ]

    def _evidence_quality_lines(self) -> list[str]:
        if self.evidence_quality_report is None:
            return [
                "- Existing evidence quality review: not run",
                "- Reason: required safe input artifacts were incomplete or unsafe.",
            ]
        report = self.evidence_quality_report
        return [
            "- Existing evidence quality review: run",
            f"- Evidence quality verdict: {report.final_readiness_verdict.value}",
            f"- Evidence source type: {report.source_type.value}",
            f"- Evidence quality score: {report.score.overall:.2f}",
            "- Evidence quality grants execution: no",
        ]


_ARTIFACT_DIR_CANDIDATES: dict[LiveArtifactKind, tuple[str, ...]] = {
    LiveArtifactKind.LIVE_FORK_CHECK: ("live_fork_check.md", "check_local_evm_fork.md"),
    LiveArtifactKind.AAVE_READONLY_DISCOVERY: ("aave_readonly_discovery.md",),
    LiveArtifactKind.EVIDENCE_PACK: ("aave_v3_evidence_pack.md", "live_fork_evidence_pack.md"),
    LiveArtifactKind.TARGET_MANIFEST: ("aave_v3_readonly.yaml", "target_manifest.yaml"),
    LiveArtifactKind.DEPENDENCY_GRAPH_REVIEW: ("dependency_graph_review.md",),
    LiveArtifactKind.TARGET_MANIFEST_REVIEW: ("target_manifest_review.md",),
    LiveArtifactKind.MANUAL_LIVE_SMOKE: ("manual_live_fork_smoke_result.md",),
    LiveArtifactKind.PHASE2B_PREFLIGHT: ("phase2b_preflight.md",),
    LiveArtifactKind.EVIDENCE_QUALITY_REPORT: ("live_fork_evidence_quality_report.md",),
}

_MANIFEST_KEYS: dict[str, LiveArtifactKind] = {
    "live_fork_check": LiveArtifactKind.LIVE_FORK_CHECK,
    "aave_readonly_discovery": LiveArtifactKind.AAVE_READONLY_DISCOVERY,
    "evidence_pack": LiveArtifactKind.EVIDENCE_PACK,
    "target_manifest": LiveArtifactKind.TARGET_MANIFEST,
    "dependency_graph_review": LiveArtifactKind.DEPENDENCY_GRAPH_REVIEW,
    "target_manifest_review": LiveArtifactKind.TARGET_MANIFEST_REVIEW,
    "manual_live_smoke": LiveArtifactKind.MANUAL_LIVE_SMOKE,
    "phase2b_preflight": LiveArtifactKind.PHASE2B_PREFLIGHT,
    "evidence_quality_report": LiveArtifactKind.EVIDENCE_QUALITY_REPORT,
}

_UNSAFE_TEXT_PATTERNS = (
    ("upstream_rpc_url", "unsafe upstream endpoint reference"),
    ("public rpc", "unsafe public endpoint reference"),
    ("private_key", "unsafe secret material reference"),
    ("private key", "unsafe secret material reference"),
    ("mnemonic", "unsafe secret material reference"),
    ("seed phrase", "unsafe secret material reference"),
    ("raw_calldata", "unsafe reusable invocation artifact"),
    ("raw calldata", "unsafe reusable invocation artifact"),
    ("calldata:", "unsafe reusable invocation artifact"),
    ("selector:", "unsafe reusable invocation artifact"),
    ("transaction bundle", "unsafe bundled execution artifact"),
    ("reusable exploit", "unsafe replayable artifact"),
    ("copy-paste attack", "unsafe replayable artifact"),
    ("live victim", "unsafe live target reference"),
    ("victim list", "unsafe live target reference"),
    ("infura", "unsafe upstream endpoint provider"),
    ("alchemy", "unsafe upstream endpoint provider"),
    ("quicknode", "unsafe upstream endpoint provider"),
    ("ankr", "unsafe upstream endpoint provider"),
    ("blastapi", "unsafe upstream endpoint provider"),
    ("publicnode", "unsafe upstream endpoint provider"),
)


def load_bundle_from_manifest(path: str | Path) -> LiveArtifactBundle:
    manifest_path = Path(path)
    if not manifest_path.exists():
        return LiveArtifactBundle({}, f"missing-manifest:{_safe_label(manifest_path)}")
    try:
        data = yaml.safe_load(manifest_path.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return LiveArtifactBundle({}, f"malformed-manifest:{_safe_label(manifest_path)}")
    if not isinstance(data, dict):
        return LiveArtifactBundle({}, f"malformed-manifest:{_safe_label(manifest_path)}")

    base_dir = manifest_path.parent
    artifact_data = data.get("artifacts", data)
    if not isinstance(artifact_data, dict):
        return LiveArtifactBundle({}, f"malformed-manifest:{_safe_label(manifest_path)}")

    artifacts: dict[LiveArtifactKind, Path] = {}
    for key, kind in _MANIFEST_KEYS.items():
        raw_path = artifact_data.get(key)
        if raw_path:
            candidate = Path(str(raw_path))
            artifacts[kind] = candidate if candidate.is_absolute() else base_dir / candidate
    return LiveArtifactBundle(artifacts, f"bundle-manifest:{_safe_label(manifest_path)}")


def load_bundle_from_artifact_dir(path: str | Path) -> LiveArtifactBundle:
    artifact_dir = Path(path)
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        return LiveArtifactBundle({}, f"missing-artifact-dir:{_safe_label(artifact_dir)}")
    artifacts: dict[LiveArtifactKind, Path] = {}
    for kind, names in _ARTIFACT_DIR_CANDIDATES.items():
        for name in names:
            candidate = artifact_dir / name
            if candidate.exists():
                artifacts[kind] = candidate
                break
    return LiveArtifactBundle(artifacts, f"artifact-dir:{_safe_label(artifact_dir)}")


def review_live_artifact_bundle(bundle: LiveArtifactBundle) -> LiveArtifactBundleReview:
    findings = [_classify_artifact(bundle, kind) for kind in LiveArtifactKind]
    safe_paths = _safe_paths_for_evidence_quality(findings, bundle)
    quality_report = None
    if safe_paths[LiveArtifactKind.EVIDENCE_PACK] and safe_paths[LiveArtifactKind.TARGET_MANIFEST]:
        if safe_paths[LiveArtifactKind.DEPENDENCY_GRAPH_REVIEW]:
            quality_report = review_evidence_quality(
                evidence_pack=safe_paths[LiveArtifactKind.EVIDENCE_PACK],
                target_manifest=safe_paths[LiveArtifactKind.TARGET_MANIFEST],
                dependency_graph_review=safe_paths[LiveArtifactKind.DEPENDENCY_GRAPH_REVIEW],
                manual_live_smoke_result=safe_paths[LiveArtifactKind.MANUAL_LIVE_SMOKE],
                phase2b_preflight_review=safe_paths[LiveArtifactKind.PHASE2B_PREFLIGHT],
            )
    review = LiveArtifactBundleReview(
        source=bundle.source,
        findings=tuple(findings),
        evidence_quality_report=quality_report,
    )
    SafetyGuard().assert_safe_report(review.to_markdown())
    return review


def _safe_paths_for_evidence_quality(
    findings: list[LiveArtifactBundleFinding],
    bundle: LiveArtifactBundle,
) -> dict[LiveArtifactKind, Path | None]:
    result: dict[LiveArtifactKind, Path | None] = {kind: None for kind in LiveArtifactKind}
    for finding in findings:
        if finding.status != LiveArtifactStatus.UNSAFE:
            result[finding.kind] = bundle.artifacts.get(finding.kind)
    return result


def _classify_artifact(
    bundle: LiveArtifactBundle,
    kind: LiveArtifactKind,
) -> LiveArtifactBundleFinding:
    path = bundle.artifacts.get(kind)
    if path is None:
        return LiveArtifactBundleFinding(
            kind=kind,
            path_label="not-provided",
            status=LiveArtifactStatus.MISSING,
            severity="review",
            note="Artifact was not provided.",
        )
    if not path.exists():
        return LiveArtifactBundleFinding(
            kind=kind,
            path_label=_safe_label(path),
            status=LiveArtifactStatus.MISSING,
            severity="review",
            note="Artifact path does not exist.",
        )
    if path.is_dir():
        return LiveArtifactBundleFinding(
            kind=kind,
            path_label=_safe_label(path),
            status=LiveArtifactStatus.MALFORMED,
            severity="blocker",
            note="Artifact path points to a directory, not a file.",
        )
    text = _read_artifact_text(path)
    if text is None:
        return LiveArtifactBundleFinding(
            kind=kind,
            path_label=_safe_label(path),
            status=LiveArtifactStatus.MALFORMED,
            severity="blocker",
            note="Artifact could not be read as text.",
        )
    unsafe_note = _unsafe_note(text)
    if unsafe_note:
        return LiveArtifactBundleFinding(
            kind=kind,
            path_label=_safe_label(path),
            status=LiveArtifactStatus.UNSAFE,
            severity="blocker",
            note=unsafe_note,
        )
    if _is_fixture_backed(text):
        return LiveArtifactBundleFinding(
            kind=kind,
            path_label=_safe_label(path),
            status=LiveArtifactStatus.FIXTURE_BACKED,
            severity="review",
            note="Artifact indicates fixture or demo mode.",
        )
    if _is_live_local_readonly(text):
        return LiveArtifactBundleFinding(
            kind=kind,
            path_label=_safe_label(path),
            status=LiveArtifactStatus.LIVE_LOCAL,
            severity="ok",
            note="Artifact indicates localhost read-only workflow.",
        )
    return LiveArtifactBundleFinding(
        kind=kind,
        path_label=_safe_label(path),
        status=LiveArtifactStatus.UNKNOWN,
        severity="review",
        note="Artifact is present but source type is not classified.",
    )


def _read_artifact_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _unsafe_note(text: str) -> str | None:
    lowered = text.lower()
    if "https://" in lowered or "http://" in lowered:
        if "http://127.0.0.1" not in lowered and "http://localhost" not in lowered:
            return "Artifact contains an unsafe endpoint reference."
    for pattern, note in _UNSAFE_TEXT_PATTERNS:
        if pattern in lowered:
            return note
    try:
        SafetyGuard().assert_safe_report(text)
    except SafetyGuardError:
        return "Artifact contains unsafe report content."
    return None


def _safe_label(path: Path) -> str:
    label = path.name or "artifact"
    lowered = label.lower()
    if _unsafe_note_for_label(lowered):
        return "sanitized-artifact-label"
    return label


def _unsafe_note_for_label(lowered: str) -> bool:
    unsafe_label_tokens = (
        "private",
        "seed",
        "mnemonic",
        "calldata",
        "bundle",
        "victim",
        "exploit",
        "infura",
        "alchemy",
        "quicknode",
        "ankr",
        "blastapi",
        "publicnode",
    )
    return any(token in lowered for token in unsafe_label_tokens)


def _is_fixture_backed(text: str) -> bool:
    lowered = text.lower()
    fixture_tokens = (
        "fixture-backed",
        "fixture_readonly",
        "fixture-only",
        "fixture local",
        "--fixture-demo",
        "fixture_review_candidate",
    )
    return any(token in lowered for token in fixture_tokens)


def _is_live_local_readonly(text: str) -> bool:
    lowered = text.lower()
    local_tokens = ("127.0.0.1", "localhost", "live-local", "local fork")
    readonly_tokens = ("read-only", "readonly", "transactions sent: no", "execution enabled: no")
    return any(token in lowered for token in local_tokens) and any(
        token in lowered for token in readonly_tokens
    )
