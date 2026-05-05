#!/usr/bin/env python3
"""Roadmap 4.35 local-only MusiCNN ONNX metadata-validation scaffold.

This CLI is intentionally stdlib-only and dry-run only. It validates recorded
artifact metadata and documented approval boundaries; it does not import or
execute production runtime, provider, TensorFlow, Essentia, or ONNX Runtime
code.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE_REPORT = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/model-provenance/local-musicnn-onnx-artifact-metadata-evidence-report.json"
)
ROADMAP_4_32_DOC = (
    SERVICE_ROOT / "docs/lightweight/roadmap-4.32-musicnn-json-metadata-diff-review-parity-readiness-gate.md"
)

SCAFFOLD_TYPE = "local-only metadata-validation"
NEXT_STEP_RECOMMENDATION = "review dry-run metadata-validation output before any inference approval"
TMP_ARTIFACT_ROOT = "/tmp/music-tools-onnx-parity/"

EXPECTED_ARTIFACTS = {
    "official_local_onnx": {
        "aliases": ("official_local_onnx",),
        "file_size_bytes": 3168334,
        "sha256": "49668ffec47e52e94b96f45930bb46a28a1368d4bdfb5c05378fa834aca616e1",
        "official_local": True,
    },
    "official_local_json": {
        "aliases": ("official_local_json",),
        "file_size_bytes": 3299,
        "sha256": "8e6b3b509f0610c0e65dce467fd459d6777509388eaddb13ed138d8ac1341ffe",
        "official_local": True,
    },
    "official_local_pb": {
        "aliases": ("official_local_pb", "optional_official_local_pb"),
        "file_size_bytes": 3197999,
        "sha256": "cdea0722bcee7f731286843f2233e3aa69887bb5c3e2dce011eff55f38d04f3e",
        "official_local": True,
    },
    "current_bundled_pb": {
        "aliases": ("current_bundled_pb",),
        "file_size_bytes": 3197999,
        "sha256": "cdea0722bcee7f731286843f2233e3aa69887bb5c3e2dce011eff55f38d04f3e",
        "official_local": False,
    },
    "current_bundled_json": {
        "aliases": ("current_bundled_json",),
        "file_size_bytes": 3298,
        "sha256": "24842b068b5c09dce033a0bcb41d450e4e469352b799e831ac7728c93bbfb6be",
        "official_local": False,
    },
}

UNEXPECTED_APPROVAL_FLAGS = (
    "approved_for_inference",
    "approved_for_production",
    "approved_for_provider_implementation",
    "approved_for_default_provider_switch",
    "approved_for_onnxruntime_dependency",
    "approved_for_runtime_migration",
    "approved_for_model_output_comparison",
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ValidationIssue(Exception):
    """Expected metadata-validation failure."""


def _base_result(evidence_report_path: Path, mode: str) -> dict[str, Any]:
    return {
        "ok": False,
        "mode": mode,
        "scaffold_type": SCAFFOLD_TYPE,
        "evidence_report_path": str(evidence_report_path),
        "inference_attempted": False,
        "onnxruntime_imported": False,
        "tensorflow_imported": False,
        "essentia_imported": False,
        "classify_called": False,
        "provider_imported": False,
        "production_runtime_touched": False,
        "checks": [],
        "warnings": [],
        "no_go_items": [],
        "next_step_recommendation": NEXT_STEP_RECOMMENDATION,
    }


def _add_check(result: dict[str, Any], name: str, ok: bool, message: str) -> None:
    result["checks"].append({"name": name, "ok": ok, "message": message})
    if not ok:
        result["no_go_items"].append(f"{name}: {message}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationIssue(f"evidence report not found: {path}") from exc
    except PermissionError as exc:
        raise ValidationIssue(f"evidence report is not readable: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationIssue(f"evidence report is not valid JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValidationIssue("evidence report JSON root must be an object")
    return data


def _artifact_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValidationIssue("artifacts must be a list")

    records = []
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise ValidationIssue(f"artifacts[{index}] must be an object")
        records.append(artifact)
    return records


def _find_artifact(artifacts: list[dict[str, Any]], aliases: tuple[str, ...]) -> dict[str, Any] | None:
    for artifact in artifacts:
        if artifact.get("artifact_role") in aliases:
            return artifact
    return None


def _iter_flag_values(value: Any, flag_name: str) -> list[Any]:
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == flag_name:
                found.append(child)
            found.extend(_iter_flag_values(child, flag_name))
    elif isinstance(value, list):
        for child in value:
            found.extend(_iter_flag_values(child, flag_name))
    return found


def _iter_text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values = []
        for child in value.values():
            values.extend(_iter_text_values(child))
        return values
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(_iter_text_values(child))
        return values
    return []


def _has_true_key(value: Any, key_name: str) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == key_name and child is True:
                return True
            if _has_true_key(child, key_name):
                return True
    elif isinstance(value, list):
        return any(_has_true_key(child, key_name) for child in value)
    return False


def _validate_artifact_metadata(
    artifacts: list[dict[str, Any]], result: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    by_expected_role: dict[str, dict[str, Any]] = {}
    missing = []
    for expected_role, expected in EXPECTED_ARTIFACTS.items():
        artifact = _find_artifact(artifacts, expected["aliases"])
        if artifact is None:
            missing.append(expected_role)
        else:
            by_expected_role[expected_role] = artifact

    if missing:
        _add_check(result, "required_artifact_roles", False, f"missing required artifact roles: {missing}")
        return by_expected_role

    _add_check(result, "required_artifact_roles", True, "required artifact roles are recorded")

    metadata_errors = []
    value_errors = []
    path_errors = []
    repo_errors = []
    for expected_role, expected in EXPECTED_ARTIFACTS.items():
        artifact = by_expected_role[expected_role]
        size = artifact.get("file_size_bytes")
        digest = artifact.get("sha256")

        if not isinstance(size, int) or size <= 0:
            metadata_errors.append(f"{expected_role}.file_size_bytes must be a positive integer")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            metadata_errors.append(f"{expected_role}.sha256 must be lowercase 64-char hex")

        if size != expected["file_size_bytes"] or digest != expected["sha256"]:
            value_errors.append(f"{expected_role} does not match recorded Roadmap 4.30 size/hash")

        if expected["official_local"]:
            local_path = artifact.get("local_path")
            if not isinstance(local_path, str) or not local_path.startswith(TMP_ARTIFACT_ROOT):
                path_errors.append(f"{expected_role}.local_path must be under {TMP_ARTIFACT_ROOT}")
            if artifact.get("artifact_in_repo") is not False:
                repo_errors.append(f"{expected_role}.artifact_in_repo must be false")
            if artifact.get("committed_to_repo") is not False:
                repo_errors.append(f"{expected_role}.committed_to_repo must be false")

    _add_check(
        result,
        "required_artifact_record_fields",
        not metadata_errors,
        "required artifact size/hash fields are well-formed" if not metadata_errors else "; ".join(metadata_errors),
    )
    _add_check(
        result,
        "roadmap_4_30_expected_values",
        not value_errors,
        "expected Roadmap 4.30 size/hash values are recorded" if not value_errors else "; ".join(value_errors),
    )
    _add_check(
        result,
        "official_local_paths_under_tmp",
        not path_errors,
        "official/local paths are recorded under /tmp/music-tools-onnx-parity/"
        if not path_errors
        else "; ".join(path_errors),
    )
    _add_check(
        result,
        "official_local_not_in_repo",
        not repo_errors,
        "official/local artifacts are recorded as not in repo and not committed"
        if not repo_errors
        else "; ".join(repo_errors),
    )
    return by_expected_role


def _validate_report_semantics(
    data: dict[str, Any], artifacts_by_role: dict[str, dict[str, Any]], result: dict[str, Any]
) -> None:
    pb_ok = False
    if {"official_local_pb", "current_bundled_pb"} <= set(artifacts_by_role):
        pb_ok = artifacts_by_role["official_local_pb"].get("sha256") == artifacts_by_role["current_bundled_pb"].get(
            "sha256"
        )
    pb_ok = pb_ok and (
        _has_true_key(data, "current_bundled_pb_matches_official_local_pb_sha256")
        or _has_true_key(data, "matches_current_bundled_pb_sha256")
    )
    _add_check(
        result,
        "pb_hash_match_observation",
        pb_ok,
        "official/local PB hash match observation is recorded"
        if pb_ok
        else "official/local PB must match current bundled PB by SHA256 and record that observation",
    )

    normalized_text = " ".join(text.casefold() for text in _iter_text_values(data))
    json_not_parity = (
        "json differs" in normalized_text
        and "not parity evidence" in normalized_text
        and "do_not_treat_json_difference_as_parity_evidence" in normalized_text
    )
    _add_check(
        result,
        "json_difference_not_parity_evidence",
        json_not_parity,
        "JSON difference is recorded as a review item, not metadata parity evidence"
        if json_not_parity
        else "JSON difference must be recorded as not parity evidence",
    )

    approval_errors = []
    for flag_name in UNEXPECTED_APPROVAL_FLAGS:
        true_values = [value for value in _iter_flag_values(data, flag_name) if value is True]
        if true_values:
            approval_errors.append(flag_name)
    _add_check(
        result,
        "unexpected_approval_flags_false",
        not approval_errors,
        "unexpected approval flags are absent or false"
        if not approval_errors
        else f"unexpected approval flags set true: {approval_errors}",
    )


def _validate_roadmap_4_32_documentation(result: dict[str, Any]) -> None:
    try:
        text = ROADMAP_4_32_DOC.read_text(encoding="utf-8").casefold()
    except OSError as exc:
        _add_check(result, "roadmap_4_32_json_equivalence_documented", False, f"unable to read Roadmap 4.32 doc: {exc}")
        return

    required_markers = (
        "parsed_json_equal=true",
        "labels_set_equal_any=true",
        "label_order_equal_any=true",
        "classification=harmless_formatting_only",
        "does not approve inference",
        "does not approve `onnxruntime`",
        "does not approve provider implementation",
        "does not approve production migration",
    )
    missing = [marker for marker in required_markers if marker not in text]
    _add_check(
        result,
        "roadmap_4_32_json_equivalence_documented",
        not missing,
        "Roadmap 4.32 JSON equivalence decision is documented"
        if not missing
        else f"Roadmap 4.32 JSON equivalence markers missing: {missing}",
    )


def run_dry_run(evidence_report_path: Path) -> dict[str, Any]:
    result = _base_result(evidence_report_path, "dry-run")
    try:
        data = _load_json(evidence_report_path)
        _add_check(result, "evidence_report_readable_json", True, "evidence report exists and is readable JSON")

        artifacts = _artifact_records(data)
        artifacts_by_role = _validate_artifact_metadata(artifacts, result)
        _validate_report_semantics(data, artifacts_by_role, result)
        _validate_roadmap_4_32_documentation(result)
    except ValidationIssue as exc:
        _add_check(result, "evidence_report_readable_json", False, str(exc))
    except OSError as exc:
        _add_check(result, "evidence_report_readable_json", False, f"unable to read evidence report: {exc}")

    result["ok"] = all(check["ok"] for check in result["checks"])
    if result["ok"]:
        result["warnings"].append("metadata-validation passed; no inference, runtime import, or production path was touched")
    else:
        result["warnings"].append("metadata-validation failed; keep all runtime and inference no-go items active")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only MusiCNN ONNX metadata-validation dry-run scaffold")
    parser.add_argument("--mode", choices=("dry-run",), default="dry-run")
    parser.add_argument("--evidence-report", type=Path, default=DEFAULT_EVIDENCE_REPORT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_dry_run(args.evidence_report)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
