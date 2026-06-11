from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.safety import SafetyGuard
from evidence.live_artifact_bundle import (
    LiveArtifactBundle,
    load_bundle_from_artifact_dir,
    load_bundle_from_manifest,
    review_live_artifact_bundle,
)
from scripts.generate_live_fork_evidence_pack import generate_evidence_pack


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review a user-provided live-local artifact bundle without enabling execution.",
    )
    parser.add_argument("--bundle-manifest")
    parser.add_argument("--artifact-dir")
    parser.add_argument("--output", default="docs/live_artifact_bundle_review.md")
    parser.add_argument(
        "--fixture-demo",
        action="store_true",
        help="Create deterministic fixture-backed artifacts for CI/demo review.",
    )
    return parser


def _fixture_demo_dir(tmpdir: str) -> Path:
    root = Path(tmpdir)
    generate_evidence_pack(
        local_rpc_url="http://127.0.0.1:8545",
        root_address="aave-root",
        network="ethereum",
        fork_block=None,
        output=str(root / "aave_v3_evidence_pack.md"),
        export_target=str(root / "aave_v3_readonly.yaml"),
        export_dependency_review=str(root / "dependency_graph_review.md"),
        fixture_readonly=True,
    )
    return root


def _load_bundle(args: argparse.Namespace):
    if args.fixture_demo:
        temp = tempfile.TemporaryDirectory()
        artifact_dir = _fixture_demo_dir(temp.name)
        bundle = load_bundle_from_artifact_dir(artifact_dir)
        return LiveArtifactBundle(bundle.artifacts, "fixture-demo"), temp
    if args.bundle_manifest:
        return load_bundle_from_manifest(args.bundle_manifest), None
    if args.artifact_dir:
        return load_bundle_from_artifact_dir(args.artifact_dir), None
    return load_bundle_from_artifact_dir("missing-live-artifact-dir"), None


def main() -> int:
    args = build_parser().parse_args()
    bundle, temp = _load_bundle(args)
    try:
        review = review_live_artifact_bundle(bundle)
        markdown = review.to_markdown()
    finally:
        if temp is not None:
            temp.cleanup()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    SafetyGuard().assert_safe_report(markdown)
    output_path.write_text(markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
