from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from core.safety import SafetyGuard


class EvidenceSourceType(str, Enum):
    MISSING = "missing"
    FIXTURE_BACKED = "fixture-backed"
    LIVE_LOCAL = "live-local"
    LIVE_LOCAL_UNAVAILABLE = "live-local-unavailable"
    UNKNOWN = "unknown"


class EvidenceReadinessVerdict(str, Enum):
    REVIEW_INCOMPLETE = "REVIEW_INCOMPLETE"
    FIXTURE_ONLY_NOT_EXECUTION_READY = "FIXTURE_ONLY_NOT_EXECUTION_READY"
    LIVE_READONLY_EVIDENCE_REVIEW_READY = "LIVE_READONLY_EVIDENCE_REVIEW_READY"
    BLOCKED_FOR_PHASE_2B = "BLOCKED_FOR_PHASE_2B"


@dataclass(frozen=True)
class EvidenceCompletenessFinding:
    artifact: str
    status: str
    severity: str
    note: str


@dataclass(frozen=True)
class ABIDecodeFinding:
    label: str
    status: str
    severity: str
    note: str


@dataclass(frozen=True)
class ABICompatibilityReport:
    decode_success_count: int
    decode_unavailable_count: int
    unresolved_call_count: int
    findings: tuple[ABIDecodeFinding, ...] = ()

    @property
    def score(self) -> float:
        total = self.decode_success_count + self.decode_unavailable_count + self.unresolved_call_count
        if total <= 0:
            return 0.0
        return round(self.decode_success_count / total, 2)


@dataclass(frozen=True)
class DiscoveryTriageItem:
    category: str
    severity: str
    note: str


@dataclass(frozen=True)
class DiscoveryTriageReport:
    items: tuple[DiscoveryTriageItem, ...] = ()

    @property
    def blocker_count(self) -> int:
        return sum(1 for item in self.items if item.severity == "blocker")


@dataclass(frozen=True)
class ReserveCoverageFinding:
    label: str
    severity: str
    note: str


@dataclass(frozen=True)
class ReserveCoverageReport:
    reserve_count: int
    max_reserves_processed: int
    truncated: bool
    unresolved_reserve_fields_count: int
    findings: tuple[ReserveCoverageFinding, ...] = ()

    @property
    def score(self) -> float:
        if self.max_reserves_processed <= 0:
            return 0.0
        base = min(self.reserve_count, self.max_reserves_processed) / self.max_reserves_processed
        if self.truncated:
            base *= 0.75
        if self.unresolved_reserve_fields_count:
            base *= 0.75
        return round(base, 2)


@dataclass(frozen=True)
class Phase2BBlocker:
    code: str
    note: str


@dataclass(frozen=True)
class Phase2BBlockerSummary:
    blockers: tuple[Phase2BBlocker, ...] = ()

    @property
    def count(self) -> int:
        return len(self.blockers)


@dataclass(frozen=True)
class EvidenceQualityScore:
    evidence_completeness: float
    source_quality: float
    abi_decode_quality: float
    reserve_coverage: float
    dependency_review_quality: float
    manifest_review_quality: float
    safety_containment: float

    @property
    def overall(self) -> float:
        values = (
            self.evidence_completeness,
            self.source_quality,
            self.abi_decode_quality,
            self.reserve_coverage,
            self.dependency_review_quality,
            self.manifest_review_quality,
            self.safety_containment,
        )
        if any(value < 0 or value > 1 for value in values):
            raise ValueError("evidence_quality_score_out_of_range")
        return round(sum(values) / len(values), 2)


@dataclass(frozen=True)
class YamlReadResult:
    data: dict[str, Any]
    status: str
    note: str


@dataclass(frozen=True)
class EvidenceQualityReport:
    source_type: EvidenceSourceType
    source_note: str
    completeness_findings: tuple[EvidenceCompletenessFinding, ...]
    abi_compatibility: ABICompatibilityReport
    reserve_coverage: ReserveCoverageReport
    dependency_review_findings: tuple[EvidenceCompletenessFinding, ...]
    target_manifest_findings: tuple[EvidenceCompletenessFinding, ...]
    triage: DiscoveryTriageReport
    phase2b_blockers: Phase2BBlockerSummary
    score: EvidenceQualityScore
    final_readiness_verdict: EvidenceReadinessVerdict

    def to_markdown(self) -> str:
        lines = [
            "# Live Fork Evidence Quality Report",
            "",
            "## 1. Summary",
            "- Phase: Phase 2A.6 — Live Fork Evidence Quality & ABI Compatibility Review",
            f"- Final readiness verdict (review-only): {self.final_readiness_verdict.value}",
            f"- Evidence quality overall score: {self.score.overall:.2f}",
            "- Execution permission granted: no",
            "- Phase 2B execution enabled: no",
            "- Review success is not execution permission.",
            "- Live-readonly review-ready means evidence can be reviewed; it never approves execution.",
            "",
            "## 2. Evidence source classification",
            f"- Evidence source type: {self.source_type.value}",
            f"- Evidence source note: {self.source_note}",
            "- Fixture-backed evidence can support CI review but cannot approve Phase 2B.",
            "",
            "## 3. Evidence completeness",
            *self._finding_lines(self.completeness_findings),
            "",
            "## 4. ABI compatibility and decode quality",
            f"- ABI decode quality score: {self.abi_compatibility.score:.2f}",
            f"- Decode success count: {self.abi_compatibility.decode_success_count}",
            f"- Decode unavailable count: {self.abi_compatibility.decode_unavailable_count}",
            f"- Unresolved call count: {self.abi_compatibility.unresolved_call_count}",
            *self._abi_lines(self.abi_compatibility.findings),
            "",
            "## 5. Aave reserve coverage",
            f"- Reserve coverage score: {self.reserve_coverage.score:.2f}",
            f"- Reserve count: {self.reserve_coverage.reserve_count}",
            f"- Max reserves processed: {self.reserve_coverage.max_reserves_processed}",
            f"- Truncated: {self._yes_no(self.reserve_coverage.truncated)}",
            f"- Unresolved reserve fields count: {self.reserve_coverage.unresolved_reserve_fields_count}",
            *self._reserve_lines(self.reserve_coverage.findings),
            "",
            "## 6. Dependency graph review quality",
            *self._finding_lines(self.dependency_review_findings),
            "",
            "## 7. Target manifest review quality",
            *self._finding_lines(self.target_manifest_findings),
            "",
            "## 8. Discovery triage items",
            *self._triage_lines(self.triage.items),
            "",
            "## 9. Phase 2B blocker summary",
            *self._blocker_lines(self.phase2b_blockers.blockers),
            "",
            "## 10. Safety and containment confirmation",
            "- Public-world side effects: forbidden",
            "- Transactions sent by this review: no",
            "- Aave Red drills executed by this review: no",
            "- Live protocol interaction by this review: no",
            "- Secret signing material included: absent",
            "- Reusable invocation artifacts included: absent",
            "- Bundled execution artifacts included: absent",
            "- Portable attack artifacts included: absent",
            "- Function-identifier artifacts included: absent",
            "",
            "## 11. Final readiness verdict",
            f"- Verdict (review-only): {self.final_readiness_verdict.value}",
            "- This verdict is not an execution approval.",
            "- Phase 2A.6 can make evidence review-ready; it cannot approve execution.",
        ]
        markdown = "\n".join(lines) + "\n"
        SafetyGuard().assert_safe_report(markdown)
        return markdown

    @staticmethod
    def _yes_no(value: bool) -> str:
        return "yes" if value else "no"

    @staticmethod
    def _finding_lines(findings: tuple[EvidenceCompletenessFinding, ...]) -> list[str]:
        if not findings:
            return ["- none"]
        return [
            f"- {finding.artifact}: {finding.status} ({finding.severity}) — {finding.note}"
            for finding in findings
        ]

    @staticmethod
    def _abi_lines(findings: tuple[ABIDecodeFinding, ...]) -> list[str]:
        if not findings:
            return ["- ABI decode findings: none"]
        return [
            f"- {finding.label}: {finding.status} ({finding.severity}) — {finding.note}"
            for finding in findings
        ]

    @staticmethod
    def _reserve_lines(findings: tuple[ReserveCoverageFinding, ...]) -> list[str]:
        if not findings:
            return ["- Reserve coverage findings: none"]
        return [f"- {finding.label}: {finding.severity} — {finding.note}" for finding in findings]

    @staticmethod
    def _triage_lines(items: tuple[DiscoveryTriageItem, ...]) -> list[str]:
        if not items:
            return ["- none"]
        return [f"- {item.category}: {item.severity} — {item.note}" for item in items]

    @staticmethod
    def _blocker_lines(blockers: tuple[Phase2BBlocker, ...]) -> list[str]:
        if not blockers:
            return ["- none"]
        return [f"- **BLOCKER** `{blocker.code}` — {blocker.note}" for blocker in blockers]


def _line_value(text: str, prefix: str, default: str = "unknown") -> str:
    for line in text.splitlines():
        if line.startswith(prefix + ":"):
            return line.split(":", 1)[1].strip()
    return default


def _int_line(text: str, prefix: str, default: int = 0) -> int:
    raw = _line_value(text, prefix, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _list_line_count(text: str, prefix: str) -> int:
    raw = _line_value(text, prefix, "none")
    if raw in {"none", "unknown", ""}:
        return 0
    return len([part.strip() for part in raw.split(",") if part.strip()])


def _bool_line(text: str, prefix: str) -> bool:
    return _line_value(text, prefix, "no").lower() == "yes"


def _safe_path_status(path: str | Path | None) -> tuple[bool, Path | None, str]:
    if not path:
        return False, None, "not-provided"
    candidate = Path(path)
    return candidate.exists(), candidate, candidate.name or "artifact"


def _read_text_if_present(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    try:
        return path.read_text()
    except OSError:
        return ""


def _read_yaml_result(path: Path | None) -> YamlReadResult:
    if path is None or not path.exists():
        return YamlReadResult({}, "missing", "Target manifest was not provided.")
    try:
        loaded = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError):
        return YamlReadResult({}, "malformed", "Target manifest could not be parsed safely.")
    if loaded is None:
        return YamlReadResult({}, "empty", "Target manifest is empty.")
    if not isinstance(loaded, dict):
        return YamlReadResult({}, "malformed", "Target manifest must be a mapping.")
    return YamlReadResult(loaded, "parsed", "Target manifest parsed as read-only review input.")


def _classify_source(evidence_text: str, manifest_data: dict[str, Any]) -> EvidenceSourceType:
    source = _line_value(evidence_text, "- Evidence source", "unknown")
    manifest_source = str(manifest_data.get("evidence_source", ""))
    deployment_sources = " ".join(str(item) for item in manifest_data.get("deployment_sources", []))
    source_blob = f"{source} {manifest_source} {deployment_sources}".lower()
    if not evidence_text:
        return EvidenceSourceType.MISSING
    if "fixture" in source_blob:
        return EvidenceSourceType.FIXTURE_BACKED
    if source == "live-local":
        return EvidenceSourceType.LIVE_LOCAL
    if source == "live-local-unavailable":
        return EvidenceSourceType.LIVE_LOCAL_UNAVAILABLE
    return EvidenceSourceType.UNKNOWN


def _manifest_metadata(data: dict[str, Any]) -> dict[str, Any]:
    metadata = data.get("protocol_metadata", {})
    if not isinstance(metadata, dict):
        return {}
    aave = metadata.get("aave_v3", {})
    return aave if isinstance(aave, dict) else {}


def _collect_manifest_unresolved_reserve_fields(metadata: dict[str, Any]) -> int:
    count = len(list(metadata.get("unresolved_reserve_fields", []) or []))
    for reserve in metadata.get("reserves", []) or []:
        if isinstance(reserve, dict):
            count += len(list(reserve.get("unresolved_fields", []) or []))
    return count


def _decode_findings(evidence_text: str, metadata: dict[str, Any]) -> ABICompatibilityReport:
    unresolved_calls = _list_line_count(evidence_text, "- Unresolved calls")
    unresolved_fields = _collect_manifest_unresolved_reserve_fields(metadata)
    discovery_status = str(
        metadata.get(
            "reserve_discovery_status",
            _line_value(evidence_text, "- Read-only discovery", "unknown"),
        )
    )
    reserves = [reserve for reserve in (metadata.get("reserves", []) or []) if isinstance(reserve, dict)]
    decode_unavailable = unresolved_calls + unresolved_fields
    findings: list[ABIDecodeFinding] = []
    success_count = 0

    for reserve in reserves:
        status_values = " ".join(
            str(reserve.get(key, ""))
            for key in ("discovery_status", "asset_price_status", "oracle_source_status")
        ).lower()
        if "unavailable" in status_values or "decode" in status_values:
            decode_unavailable += 1
            findings.append(
                ABIDecodeFinding(
                    label="reserve_decode",
                    status="decode_unavailable",
                    severity="review",
                    note="Reserve metadata contains decode-unavailable status.",
                )
            )
        else:
            success_count += 1

    if unresolved_calls:
        findings.append(
            ABIDecodeFinding(
                label="unresolved_calls",
                status="unresolved",
                severity="review",
                note="Read-only discovery reported unresolved safe call labels.",
            )
        )
    if unresolved_fields:
        findings.append(
            ABIDecodeFinding(
                label="unresolved_reserve_fields",
                status="unresolved",
                severity="review",
                note="Reserve metadata contains unresolved fields requiring triage.",
            )
        )
    if discovery_status not in {"fully_discovered", "full"}:
        findings.append(
            ABIDecodeFinding(
                label="discovery_status",
                status=discovery_status,
                severity="review",
                note="Read-only discovery is not fully decoded.",
            )
        )
    if success_count == 0 and not findings:
        findings.append(
            ABIDecodeFinding(
                label="abi_decode_evidence",
                status="missing",
                severity="blocker",
                note="No reserve decode evidence is available for review.",
            )
        )

    return ABICompatibilityReport(
        decode_success_count=success_count,
        decode_unavailable_count=decode_unavailable,
        unresolved_call_count=unresolved_calls,
        findings=tuple(findings),
    )


def _reserve_coverage(evidence_text: str, metadata: dict[str, Any]) -> ReserveCoverageReport:
    reserve_count = int(metadata.get("reserve_count", 0) or _int_line(evidence_text, "- Reserve count"))
    max_processed = int(
        metadata.get("max_reserves_processed", 0)
        or _int_line(evidence_text, "- Max reserves processed")
    )
    truncated = bool(metadata.get("truncated", False) or _bool_line(evidence_text, "- Truncated"))
    unresolved = _collect_manifest_unresolved_reserve_fields(metadata)
    findings: list[ReserveCoverageFinding] = []

    if reserve_count == 0:
        findings.append(ReserveCoverageFinding("reserve_count", "blocker", "No reserve metadata was available."))
    if max_processed and reserve_count < max_processed:
        findings.append(
            ReserveCoverageFinding(
                "reserve_coverage_gap",
                "review",
                "Discovered reserve count is below the configured processed reserve window.",
            )
        )
    if truncated:
        findings.append(
            ReserveCoverageFinding(
                "reserve_truncation",
                "review",
                "Reserve discovery was truncated and requires coverage review.",
            )
        )
    if unresolved:
        findings.append(
            ReserveCoverageFinding(
                "unresolved_reserve_fields",
                "review",
                "Unresolved reserve fields require ABI/decode triage before Phase 2B.",
            )
        )

    return ReserveCoverageReport(
        reserve_count=reserve_count,
        max_reserves_processed=max_processed,
        truncated=truncated,
        unresolved_reserve_fields_count=unresolved,
        findings=tuple(findings),
    )


def _blockers_unique(blockers: list[Phase2BBlocker]) -> tuple[Phase2BBlocker, ...]:
    seen: set[str] = set()
    unique: list[Phase2BBlocker] = []
    for blocker in blockers:
        if blocker.code not in seen:
            seen.add(blocker.code)
            unique.append(blocker)
    return tuple(unique)


def review_evidence_quality(
    *,
    evidence_pack: str | Path | None,
    target_manifest: str | Path | None,
    dependency_graph_review: str | Path | None,
    manual_live_smoke_result: str | Path | None = None,
    phase2b_preflight_review: str | Path | None = None,
) -> EvidenceQualityReport:
    evidence_exists, evidence_path, evidence_label = _safe_path_status(evidence_pack)
    target_exists, target_path, target_label = _safe_path_status(target_manifest)
    dep_exists, dep_path, dep_label = _safe_path_status(dependency_graph_review)
    smoke_exists, _smoke_path, smoke_label = _safe_path_status(manual_live_smoke_result)
    preflight_exists, preflight_path, preflight_label = _safe_path_status(phase2b_preflight_review)

    evidence_text = _read_text_if_present(evidence_path)
    dep_text = _read_text_if_present(dep_path)
    preflight_text = _read_text_if_present(preflight_path)
    manifest_result = _read_yaml_result(target_path)
    manifest_data = manifest_result.data
    metadata = _manifest_metadata(manifest_data)
    source_type = _classify_source(evidence_text, manifest_data)

    completeness = [
        EvidenceCompletenessFinding(
            evidence_label,
            "present" if evidence_exists else "missing",
            "blocker" if not evidence_exists else "ok",
            "LiveForkEvidencePack markdown input.",
        ),
        EvidenceCompletenessFinding(
            target_label,
            "present" if target_exists else "missing",
            "blocker" if not target_exists else "ok",
            "Exported target manifest input.",
        ),
        EvidenceCompletenessFinding(
            dep_label,
            "present" if dep_exists else "missing",
            "blocker" if not dep_exists else "ok",
            "Dependency graph review input.",
        ),
        EvidenceCompletenessFinding(
            smoke_label,
            "present" if smoke_exists else "missing",
            "review" if not smoke_exists else "ok",
            "Manual live fork smoke result is optional for CI but required for live readiness review.",
        ),
        EvidenceCompletenessFinding(
            preflight_label,
            "present" if preflight_exists else "missing",
            "review" if not preflight_exists else "ok",
            "Phase 2B preflight output is optional review evidence and never execution permission.",
        ),
    ]

    abi_report = _decode_findings(evidence_text, metadata)
    reserve_report = _reserve_coverage(evidence_text, metadata)

    dependency_findings = _dependency_findings(dep_exists, dep_label, dep_text)
    manifest_findings = _manifest_findings(target_exists, target_label, manifest_result)
    triage_items = _triage_items(
        source_type=source_type,
        smoke_exists=smoke_exists,
        preflight_exists=preflight_exists,
        preflight_text=preflight_text,
        abi_report=abi_report,
        reserve_report=reserve_report,
        dependency_findings=dependency_findings,
        manifest_findings=manifest_findings,
    )
    blockers = _phase2b_blockers(
        source_type=source_type,
        smoke_exists=smoke_exists,
        preflight_exists=preflight_exists,
        preflight_text=preflight_text,
        completeness=completeness,
        dependency_findings=dependency_findings,
        manifest_findings=manifest_findings,
        abi_report=abi_report,
        reserve_report=reserve_report,
    )
    verdict = _final_verdict(
        evidence_exists=evidence_exists,
        target_exists=target_exists,
        dep_exists=dep_exists,
        source_type=source_type,
        smoke_exists=smoke_exists,
        manifest_findings=manifest_findings,
    )

    dep_status = _line_value(dep_text, "- Review status", "missing" if not dep_exists else "unknown")
    completeness_score = sum(1 for finding in completeness if finding.status == "present") / len(completeness)
    source_score = {EvidenceSourceType.LIVE_LOCAL: 1.0, EvidenceSourceType.FIXTURE_BACKED: 0.5}.get(
        source_type,
        0.0,
    )
    dep_score = 0.0 if not dep_exists else (0.5 if "fixture" in dep_status or "insufficient" in dep_status else 1.0)
    manifest_score = 0.0 if not target_exists else (1.0 if manifest_data.get("read_only_only") is True else 0.0)

    report = EvidenceQualityReport(
        source_type=source_type,
        source_note=_source_note(source_type),
        completeness_findings=tuple(completeness),
        abi_compatibility=abi_report,
        reserve_coverage=reserve_report,
        dependency_review_findings=tuple(dependency_findings),
        target_manifest_findings=tuple(manifest_findings),
        triage=DiscoveryTriageReport(tuple(triage_items)),
        phase2b_blockers=Phase2BBlockerSummary(_blockers_unique(blockers)),
        score=EvidenceQualityScore(
            evidence_completeness=round(completeness_score, 2),
            source_quality=source_score,
            abi_decode_quality=abi_report.score,
            reserve_coverage=reserve_report.score,
            dependency_review_quality=dep_score,
            manifest_review_quality=manifest_score,
            safety_containment=1.0,
        ),
        final_readiness_verdict=verdict,
    )
    SafetyGuard().assert_safe_report(report.to_markdown())
    return report


def _dependency_findings(
    dep_exists: bool,
    dep_label: str,
    dep_text: str,
) -> list[EvidenceCompletenessFinding]:
    dep_status = _line_value(dep_text, "- Review status", "missing" if not dep_exists else "unknown")
    if not dep_exists:
        return [
            EvidenceCompletenessFinding(
                dep_label,
                "missing",
                "blocker",
                "Dependency graph review is required.",
            )
        ]

    severity = "review" if "fixture" in dep_status or "insufficient" in dep_status else "ok"
    findings = [
        EvidenceCompletenessFinding(
            dep_label,
            dep_status,
            severity,
            "Dependency graph review candidate status.",
        )
    ]
    if _int_line(dep_text, "- Unresolved reserve fields count"):
        findings.append(
            EvidenceCompletenessFinding(
                "dependency_unresolved_items",
                "present",
                "review",
                "Dependency review contains unresolved reserve fields.",
            )
        )
    return findings


def _manifest_findings(
    target_exists: bool,
    target_label: str,
    manifest_result: YamlReadResult,
) -> list[EvidenceCompletenessFinding]:
    if not target_exists:
        return [
            EvidenceCompletenessFinding(
                target_label,
                "missing",
                "blocker",
                "Target manifest is required.",
            )
        ]

    findings: list[EvidenceCompletenessFinding] = [
        EvidenceCompletenessFinding(
            "manifest_parse_status",
            manifest_result.status,
            "ok" if manifest_result.status == "parsed" else "blocker",
            manifest_result.note,
        )
    ]
    if manifest_result.status != "parsed":
        return findings

    manifest_data = manifest_result.data
    read_only = bool(manifest_data.get("read_only_only", False))
    executable_allowed = bool(manifest_data.get("executable_drills_allowed", False))
    scope_confirmed = bool(manifest_data.get("scope_confirmed", False))
    findings.append(
        EvidenceCompletenessFinding(
            target_label,
            "read_only" if read_only else "not_read_only",
            "ok" if read_only else "blocker",
            "Manifest must remain read-only in Phase 2A.6.",
        )
    )
    findings.append(
        EvidenceCompletenessFinding(
            "scope_confirmation",
            "confirmed" if scope_confirmed else "unconfirmed",
            "review",
            "Scope confirmation is reviewer-controlled and does not grant execution.",
        )
    )
    if executable_allowed:
        findings.append(
            EvidenceCompletenessFinding(
                "executable_drills_allowed",
                "true",
                "blocker",
                "Phase 2A.6 must not allow executable fork drills.",
            )
        )
    return findings


def _triage_items(
    *,
    source_type: EvidenceSourceType,
    smoke_exists: bool,
    preflight_exists: bool,
    preflight_text: str,
    abi_report: ABICompatibilityReport,
    reserve_report: ReserveCoverageReport,
    dependency_findings: list[EvidenceCompletenessFinding],
    manifest_findings: list[EvidenceCompletenessFinding],
) -> list[DiscoveryTriageItem]:
    items: list[DiscoveryTriageItem] = []
    if source_type == EvidenceSourceType.FIXTURE_BACKED:
        items.append(
            DiscoveryTriageItem(
                "evidence_source",
                "review",
                "Fixture-backed evidence is CI-useful but cannot approve Phase 2B.",
            )
        )
    if source_type in {
        EvidenceSourceType.MISSING,
        EvidenceSourceType.UNKNOWN,
        EvidenceSourceType.LIVE_LOCAL_UNAVAILABLE,
    }:
        items.append(
            DiscoveryTriageItem(
                "live_evidence",
                "blocker",
                "Live local read-only evidence is missing, unavailable, or unclassified.",
            )
        )
    if not smoke_exists:
        items.append(
            DiscoveryTriageItem(
                "manual_live_smoke",
                "review",
                "Manual live fork smoke evidence was not provided.",
            )
        )
    if not preflight_exists:
        items.append(
            DiscoveryTriageItem(
                "phase2b_preflight",
                "review",
                "Phase 2B preflight output was not provided.",
            )
        )
    elif "execution enabled: no" not in preflight_text.lower():
        items.append(
            DiscoveryTriageItem(
                "phase2b_preflight",
                "blocker",
                "Preflight evidence must show execution remains disabled.",
            )
        )

    for finding in abi_report.findings:
        items.append(DiscoveryTriageItem("abi_decode", finding.severity, finding.note))
    for finding in reserve_report.findings:
        items.append(DiscoveryTriageItem("reserve_coverage", finding.severity, finding.note))
    for finding in dependency_findings + manifest_findings:
        if finding.severity in {"review", "blocker"}:
            items.append(DiscoveryTriageItem(finding.artifact, finding.severity, finding.note))
    return items


def _phase2b_blockers(
    *,
    source_type: EvidenceSourceType,
    smoke_exists: bool,
    preflight_exists: bool,
    preflight_text: str,
    completeness: list[EvidenceCompletenessFinding],
    dependency_findings: list[EvidenceCompletenessFinding],
    manifest_findings: list[EvidenceCompletenessFinding],
    abi_report: ABICompatibilityReport,
    reserve_report: ReserveCoverageReport,
) -> list[Phase2BBlocker]:
    blockers = [
        Phase2BBlocker(
            "phase2b_execution_gate_absent",
            "A separate explicitly approved Phase 2B gate is still required.",
        ),
        Phase2BBlocker(
            "execution_permission_not_granted",
            "This evidence review does not grant execution permission.",
        ),
    ]
    if source_type == EvidenceSourceType.FIXTURE_BACKED:
        blockers.append(Phase2BBlocker("fixture_only_evidence", "Fixture-backed evidence cannot approve Phase 2B."))
    if source_type != EvidenceSourceType.LIVE_LOCAL:
        blockers.append(
            Phase2BBlocker(
                "live_local_readonly_evidence_missing",
                "Live local read-only evidence is not present.",
            )
        )
    if not smoke_exists:
        blockers.append(Phase2BBlocker("manual_live_smoke_missing", "Manual live fork smoke result is missing."))
    if preflight_exists and "execution enabled: no" not in preflight_text.lower():
        blockers.append(
            Phase2BBlocker(
                "preflight_execution_state_unclear",
                "Preflight evidence must show execution remains disabled.",
            )
        )
    if any(finding.severity == "blocker" for finding in completeness + dependency_findings + manifest_findings):
        blockers.append(
            Phase2BBlocker(
                "required_review_artifact_missing",
                "One or more required review artifacts are missing, malformed, or unsafe.",
            )
        )
    if any(finding.severity == "blocker" for finding in abi_report.findings):
        blockers.append(Phase2BBlocker("discovery_quality_blocker", "Discovery quality has blocker-level gaps."))
    if any(finding.severity == "blocker" for finding in reserve_report.findings):
        blockers.append(Phase2BBlocker("reserve_quality_blocker", "Reserve coverage has blocker-level gaps."))
    return blockers


def _final_verdict(
    *,
    evidence_exists: bool,
    target_exists: bool,
    dep_exists: bool,
    source_type: EvidenceSourceType,
    smoke_exists: bool,
    manifest_findings: list[EvidenceCompletenessFinding],
) -> EvidenceReadinessVerdict:
    required_present = evidence_exists and target_exists and dep_exists
    if not required_present:
        return EvidenceReadinessVerdict.REVIEW_INCOMPLETE
    if any(finding.artifact == "executable_drills_allowed" for finding in manifest_findings):
        return EvidenceReadinessVerdict.BLOCKED_FOR_PHASE_2B
    if any(finding.artifact == "manifest_parse_status" and finding.severity == "blocker" for finding in manifest_findings):
        return EvidenceReadinessVerdict.REVIEW_INCOMPLETE
    if source_type == EvidenceSourceType.FIXTURE_BACKED:
        return EvidenceReadinessVerdict.FIXTURE_ONLY_NOT_EXECUTION_READY
    if source_type == EvidenceSourceType.LIVE_LOCAL and smoke_exists:
        return EvidenceReadinessVerdict.LIVE_READONLY_EVIDENCE_REVIEW_READY
    return EvidenceReadinessVerdict.BLOCKED_FOR_PHASE_2B


def _source_note(source_type: EvidenceSourceType) -> str:
    return {
        EvidenceSourceType.MISSING: "Evidence pack is missing.",
        EvidenceSourceType.FIXTURE_BACKED: "Fixture-backed evidence is useful for CI but not execution readiness.",
        EvidenceSourceType.LIVE_LOCAL: "Live local read-only evidence is present for review only, not execution.",
        EvidenceSourceType.LIVE_LOCAL_UNAVAILABLE: "Live local evidence was attempted but unavailable.",
        EvidenceSourceType.UNKNOWN: "Evidence source could not be classified safely.",
    }[source_type]
