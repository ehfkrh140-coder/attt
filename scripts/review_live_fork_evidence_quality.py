from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.safety import SafetyGuard
from evidence.evidence_quality import review_evidence_quality
from scripts.generate_live_fork_evidence_pack import generate_evidence_pack


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review Phase 2A.5 live fork evidence quality without enabling execution.",
        epilog=(
            "Missing artifact paths are reported as review findings in the markdown output. "
            "Use --fixture-demo for deterministic CI/demo inputs. This command never sends transactions."
        ),
    )
    parser.add_argument("--evidence-pack")
    parser.add_argument("--target-manifest")
    parser.add_argument("--dependency-graph-review")
    parser.add_argument("--manual-live-smoke-result")
    parser.add_argument("--phase2b-preflight")
    parser.add_argument("--output", default="docs/live_fork_evidence_quality_report.md")
    parser.add_argument(
        "--fixture-demo",
        action="store_true",
        help="Generate fixture-backed inputs for deterministic CI/demo review.",
    )
    return parser


def _fixture_demo_paths(tmpdir: str) -> tuple[Path, Path, Path]:
    root = Path(tmpdir)
    evidence_path = root / "aave_v3_evidence_pack.md"
    target_path = root / "aave_v3_readonly.yaml"
    dependency_path = root / "dependency_graph_review.md"
    generate_evidence_pack(
        local_rpc_url="http://127.0.0.1:8545",
        root_address="aave-root",
        network="ethereum",
        fork_block=None,
        output=str(evidence_path),
        export_target=str(target_path),
        export_dependency_review=str(dependency_path),
        fixture_readonly=True,
    )
    return evidence_path, target_path, dependency_path


def _safe_missing_input_notes(args: argparse.Namespace) -> list[str]:
    if args.fixture_demo:
        return []
    expected = (
        ("evidence pack", args.evidence_pack),
        ("target manifest", args.target_manifest),
        ("dependency graph review", args.dependency_graph_review),
    )
    return [f"- CLI note: missing {label}; report will mark it as a review finding." for label, value in expected if not value]


def main() -> int:
    args = build_parser().parse_args()
    if args.fixture_demo:
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_path, target_path, dependency_path = _fixture_demo_paths(tmpdir)
            report = review_evidence_quality(
                evidence_pack=evidence_path,
                target_manifest=target_path,
                dependency_graph_review=dependency_path,
                manual_live_smoke_result=args.manual_live_smoke_result,
                phase2b_preflight_review=args.phase2b_preflight,
            )
    else:
        report = review_evidence_quality(
            evidence_pack=args.evidence_pack,
            target_manifest=args.target_manifest,
            dependency_graph_review=args.dependency_graph_review,
            manual_live_smoke_result=args.manual_live_smoke_result,
            phase2b_preflight_review=args.phase2b_preflight,
        )

    markdown = report.to_markdown()
    notes = _safe_missing_input_notes(args)
    if notes:
        markdown = markdown.rstrip() + "\n\n## CLI input notes\n" + "\n".join(notes) + "\n"

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    SafetyGuard().assert_safe_report(markdown)
    output_path.write_text(markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
