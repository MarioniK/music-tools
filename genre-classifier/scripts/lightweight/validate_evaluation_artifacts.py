#!/usr/bin/env python3
"""Validate Roadmap 4.3 lightweight evaluation example artifacts.

This is an offline-only, dependency-free shape validator for documentation
artifacts. It intentionally does not import production app, provider, runtime,
or inference code.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, NamedTuple


EVALUATION_DIR = Path("docs/lightweight/evaluation")

REQUIRED_FILES = (
    Path("README.md"),
    Path("manifests/example-manifest.yaml"),
    Path("outputs/example-legacy-baseline-output.json"),
    Path("outputs/example-candidate-output.json"),
    Path("reports/example-evaluation-report.md"),
)

OUTPUT_FILES = (
    Path("outputs/example-legacy-baseline-output.json"),
    Path("outputs/example-candidate-output.json"),
)

MODEL_PROVENANCE_FILES = (
    Path("model-provenance/example-onnx-model-provenance.json"),
)

LABEL_MAPPING_FILES = (
    Path("label-mapping/example-onnx-label-mapping.json"),
)

REQUIRED_MODEL_PROVENANCE_FIELDS = (
    "schema_version",
    "model_id",
    "model_name",
    "model_family",
    "model_format",
    "source_url",
    "source_repository",
    "license",
    "license_url",
    "model_version",
    "model_hash_sha256",
    "model_file_name",
    "model_file_size_bytes",
    "input_names",
    "input_shapes",
    "output_names",
    "output_shapes",
    "label_source",
    "label_count",
    "label_mapping_strategy",
    "intended_use",
    "known_limitations",
    "approval_status",
    "warnings",
)

MODEL_PROVENANCE_STRING_FIELDS = (
    "schema_version",
    "model_id",
    "model_name",
    "model_family",
    "model_format",
    "source_url",
    "source_repository",
    "license",
    "license_url",
    "model_version",
    "model_hash_sha256",
    "model_file_name",
    "label_source",
    "label_mapping_strategy",
    "intended_use",
    "approval_status",
)

PRODUCTION_APPROVED_STATUSES = {
    "approved",
    "approved_for_inference",
    "production_approved",
    "production-approved",
}

REQUIRED_LABEL_MAPPING_FIELDS = (
    "schema_version",
    "mapping_id",
    "model_id",
    "model_family",
    "label_source",
    "label_source_url",
    "label_count",
    "mapping_status",
    "labels",
    "controlled_vocabulary_version",
    "unmapped_labels",
    "warnings",
    "approval_status",
)

LABEL_MAPPING_STRING_FIELDS = (
    "schema_version",
    "mapping_id",
    "model_id",
    "model_family",
    "label_source",
    "label_source_url",
    "mapping_status",
    "controlled_vocabulary_version",
    "approval_status",
)

REQUIRED_LABEL_MAPPING_LABEL_FIELDS = (
    "raw_label",
    "raw_index",
    "mapped_genre",
    "mapped_confidence",
    "mapping_decision",
    "mapping_notes",
)

LABEL_MAPPING_DECISIONS = {
    "mapped",
    "alias_mapped",
    "ignored_non_genre",
    "unmapped",
    "rejected_ambiguous",
}

LABEL_MAPPING_APPROVAL_STATUSES = {
    "not_approved",
    "approved_for_offline_evaluation",
    "rejected",
    "deprecated",
}

MANIFEST_MARKERS = (
    'schema_version: "0.1"',
    'artifact_type: "example_manifest_skeleton"',
    'manifest_id: "example_lightweight_eval_manifest_v0_1"',
    "fixtures:",
    'category: "clear_mainstream_genres"',
    'category: "negative_edge_fixtures"',
)

REPORT_MARKERS = (
    "# Example Lightweight Evaluation Report",
    "Status: example skeleton only",
    "## Production Contract",
    "`legacy_musicnn` remains the production baseline and default provider.",
    "## Approval Gate Status",
)

REQUIRED_REPORT_MARKERS = (
    "summary",
    "scope",
    "baseline provider",
    "candidate provider",
    "manifest",
    "fixture coverage",
    "aggregate comparison",
    "controlled vocabulary results",
    "oov results",
    "top-n overlap",
    "resource metrics",
    "failures and warnings",
    "known gaps",
    "decision",
    "approval gate status",
    "appendix",
    "per-fixture results",
)

KNOWN_WARNING_CATEGORIES = (
    "fixture_missing",
    "fixture_unreadable",
    "baseline_failed",
    "candidate_failed",
    "empty_output",
    "oov_terms_detected",
    "major_genre_shift",
    "license_unknown",
    "model_provenance_unknown",
    "runtime_metric_missing",
    "comparison_incomplete",
)

README_MARKERS = (
    "# Lightweight Evaluation Artifacts",
    "The `/classify` contract is unchanged.",
    "- `ok`",
    "- `message`",
    "- `genres`",
    "- `genres_pretty`",
)


class ValidationError(Exception):
    """Raised when an artifact does not match the expected example shape."""


class ValidationSummary(NamedTuple):
    files_checked: int
    json_outputs_checked: int
    fixture_results_checked: int
    model_provenance_checked: int = 0
    label_mapping_checked: int = 0


class GenreOverlapSummary(NamedTuple):
    baseline_count: int
    candidate_count: int
    overlap_count: int
    overlap_ratio: float
    baseline_empty: bool
    candidate_empty: bool


def _read_non_empty_text(path: Path) -> str:
    if not path.exists():
        raise ValidationError(f"Missing required artifact: {path}")
    if not path.is_file():
        raise ValidationError(f"Required artifact is not a file: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValidationError(f"Required artifact is empty: {path}")
    return text


def _validate_markers(path: Path, text: str, markers: Iterable[str]) -> None:
    for marker in markers:
        if marker not in text:
            raise ValidationError(f"Missing marker in {path}: {marker!r}")


def _normalize_report_text(text: str) -> str:
    return " ".join(text.casefold().split())


def _validate_normalized_report_markers(path: Path, text: str, markers: Iterable[str]) -> None:
    normalized_text = _normalize_report_text(text)
    for marker in markers:
        normalized_marker = _normalize_report_text(marker)
        if normalized_marker not in normalized_text:
            raise ValidationError(f"Missing report section or marker in {path}: {marker!r}")


def _validate_report(path: Path) -> None:
    text = _read_non_empty_text(path)
    _validate_markers(path, text, REPORT_MARKERS)
    _validate_normalized_report_markers(path, text, REQUIRED_REPORT_MARKERS)
    _validate_normalized_report_markers(path, text, KNOWN_WARNING_CATEGORIES)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(_read_non_empty_text(path))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(value, dict):
        raise ValidationError(f"JSON artifact must be an object: {path}")
    return value


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_warnings(value: dict[str, Any], context: str) -> None:
    if "warnings" not in value:
        return

    warnings = value["warnings"]
    if not isinstance(warnings, list):
        raise ValidationError(f"{context}.warnings must be a list when present")

    for index, item in enumerate(warnings):
        item_context = f"{context}.warnings[{index}]"
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            raise ValidationError(f"{item_context} must be a string or object")

        category = item.get("category")
        if category is not None and (not isinstance(category, str) or not category.strip()):
            raise ValidationError(f"{item_context}.category must be a non-empty string when present")


def _validate_classify_response_shape(value: dict[str, Any], context: str) -> None:
    required_fields = ("ok", "message", "genres", "genres_pretty")
    for field in required_fields:
        if field not in value:
            raise ValidationError(f"{context} is missing required field: {field}")

    if not isinstance(value["ok"], bool):
        raise ValidationError(f"{context}.ok must be a bool")
    if not isinstance(value["message"], str):
        raise ValidationError(f"{context}.message must be a string")
    if not isinstance(value["genres"], list):
        raise ValidationError(f"{context}.genres must be a list")
    if not isinstance(value["genres_pretty"], list):
        raise ValidationError(f"{context}.genres_pretty must be a list")

    for index, item in enumerate(value["genres_pretty"]):
        if not isinstance(item, str):
            raise ValidationError(f"{context}.genres_pretty[{index}] must be a string")

    for index, item in enumerate(value["genres"]):
        item_context = f"{context}.genres[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"{item_context} must be an object")
        for field in ("tag", "prob"):
            if field not in item:
                raise ValidationError(f"{item_context} is missing required field: {field}")

        tag = item["tag"]
        if not isinstance(tag, str) or not tag.strip():
            raise ValidationError(f"{item_context}.tag must be a non-empty string")

        prob = item["prob"]
        if not _is_number(prob):
            raise ValidationError(f"{item_context}.prob must be an int or float")
        if not 0 <= prob <= 1:
            raise ValidationError(f"{item_context}.prob must be in range 0..1")

    _validate_warnings(value, context)


def _validate_output(path: Path) -> int:
    data = _load_json(path)
    _validate_warnings(data, str(path))

    fixture_results = data.get("fixture_results")
    if not isinstance(fixture_results, list) or not fixture_results:
        raise ValidationError(f"{path}.fixture_results must be a non-empty list")

    for index, result in enumerate(fixture_results):
        if not isinstance(result, dict):
            raise ValidationError(f"{path}.fixture_results[{index}] must be an object")
        _validate_classify_response_shape(result, f"{path}.fixture_results[{index}]")

    return len(fixture_results)


def _validate_model_provenance(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_MODEL_PROVENANCE_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required provenance field: {field}")

    for field in MODEL_PROVENANCE_STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    if data["model_format"] != "onnx":
        raise ValidationError(f'{path}.model_format must be "onnx"')

    for field in ("input_names", "output_names", "known_limitations", "warnings"):
        if not isinstance(data[field], list):
            raise ValidationError(f"{path}.{field} must be a list")

    for field in ("input_shapes", "output_shapes"):
        value = data[field]
        if not isinstance(value, list):
            raise ValidationError(f"{path}.{field} must be a list")
        for index, item in enumerate(value):
            if not isinstance(item, list):
                raise ValidationError(f"{path}.{field}[{index}] must be a list")

    for field in ("model_file_size_bytes", "label_count"):
        value = data[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValidationError(f"{path}.{field} must be a non-negative integer")

    _validate_warnings(data, str(path))

    approval_status = data["approval_status"].strip().casefold()
    if approval_status in PRODUCTION_APPROVED_STATUSES:
        raise ValidationError(f"{path}.approval_status must not be production-approved")


def _validate_label_mapping(path: Path) -> None:
    data = _load_json(path)

    for field in REQUIRED_LABEL_MAPPING_FIELDS:
        if field not in data:
            raise ValidationError(f"{path} is missing required label mapping field: {field}")

    for field in LABEL_MAPPING_STRING_FIELDS:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    label_count = data["label_count"]
    if not isinstance(label_count, int) or isinstance(label_count, bool) or label_count < 0:
        raise ValidationError(f"{path}.label_count must be a non-negative integer")

    labels = data["labels"]
    if not isinstance(labels, list) or not labels:
        raise ValidationError(f"{path}.labels must be a non-empty list")
    if len(labels) != label_count:
        raise ValidationError(f"{path}.label_count must match labels length")

    for field in ("unmapped_labels", "warnings"):
        if not isinstance(data[field], list):
            raise ValidationError(f"{path}.{field} must be a list")

    _validate_warnings(data, str(path))

    approval_status = data["approval_status"].strip()
    if approval_status not in LABEL_MAPPING_APPROVAL_STATUSES:
        raise ValidationError(f"{path}.approval_status is not a documented label mapping status")

    raw_indexes: set[int] = set()
    seen_decisions: set[str] = set()
    for index, item in enumerate(labels):
        item_context = f"{path}.labels[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"{item_context} must be an object")

        for field in REQUIRED_LABEL_MAPPING_LABEL_FIELDS:
            if field not in item:
                raise ValidationError(f"{item_context} is missing required field: {field}")

        raw_label = item["raw_label"]
        if not isinstance(raw_label, str) or not raw_label.strip():
            raise ValidationError(f"{item_context}.raw_label must be a non-empty string")

        raw_index = item["raw_index"]
        if not isinstance(raw_index, int) or isinstance(raw_index, bool) or raw_index < 0:
            raise ValidationError(f"{item_context}.raw_index must be a non-negative integer")
        if raw_index in raw_indexes:
            raise ValidationError(f"{item_context}.raw_index must be unique")
        raw_indexes.add(raw_index)

        for field in ("mapped_genre", "mapped_confidence", "mapping_notes"):
            if not isinstance(item[field], str):
                raise ValidationError(f"{item_context}.{field} must be a string")

        decision = item["mapping_decision"]
        if decision not in LABEL_MAPPING_DECISIONS:
            raise ValidationError(f"{item_context}.mapping_decision is not allowed: {decision!r}")
        seen_decisions.add(decision)

        if decision in {"mapped", "alias_mapped"} and not item["mapped_genre"].strip():
            raise ValidationError(f"{item_context}.mapped_genre must be non-empty for mapped decisions")
        if decision in {"ignored_non_genre", "unmapped", "rejected_ambiguous"} and item["mapped_genre"].strip():
            raise ValidationError(f"{item_context}.mapped_genre must be empty for non-mapped decisions")

    missing_decisions = LABEL_MAPPING_DECISIONS - seen_decisions
    if missing_decisions:
        raise ValidationError(f"{path}.labels does not demonstrate decisions: {sorted(missing_decisions)}")


def _extract_genre_tags(value: dict[str, Any]) -> set[str]:
    fixture_results = value.get("fixture_results")
    if isinstance(fixture_results, list):
        results = fixture_results
    else:
        results = [value]

    tags: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            continue
        genres = result.get("genres")
        if not isinstance(genres, list):
            continue
        for item in genres:
            if not isinstance(item, dict):
                continue
            tag = item.get("tag")
            if isinstance(tag, str) and tag.strip():
                tags.add(tag.strip().casefold())
    return tags


def compare_genre_overlap(baseline: dict[str, Any], candidate: dict[str, Any]) -> GenreOverlapSummary:
    baseline_tags = _extract_genre_tags(baseline)
    candidate_tags = _extract_genre_tags(candidate)
    overlap_count = len(baseline_tags & candidate_tags)
    denominator = max(len(baseline_tags), len(candidate_tags))
    overlap_ratio = overlap_count / denominator if denominator else 0.0

    return GenreOverlapSummary(
        baseline_count=len(baseline_tags),
        candidate_count=len(candidate_tags),
        overlap_count=overlap_count,
        overlap_ratio=overlap_ratio,
        baseline_empty=not baseline_tags,
        candidate_empty=not candidate_tags,
    )


def compare_output_files(baseline_path: Path, candidate_path: Path) -> GenreOverlapSummary:
    return compare_genre_overlap(_load_json(baseline_path), _load_json(candidate_path))


def validate_all(root: Path) -> ValidationSummary:
    evaluation_root = root / EVALUATION_DIR
    for relative_path in REQUIRED_FILES:
        _read_non_empty_text(evaluation_root / relative_path)

    readme_path = evaluation_root / "README.md"
    _validate_markers(readme_path, _read_non_empty_text(readme_path), README_MARKERS)

    manifest_path = evaluation_root / "manifests/example-manifest.yaml"
    manifest_text = _read_non_empty_text(manifest_path)
    # Full YAML schema validation is a future step for the real offline harness.
    _validate_markers(manifest_path, manifest_text, MANIFEST_MARKERS)

    report_path = evaluation_root / "reports/example-evaluation-report.md"
    _validate_report(report_path)

    fixture_result_count = 0
    for relative_path in OUTPUT_FILES:
        fixture_result_count += _validate_output(evaluation_root / relative_path)

    model_provenance_count = 0
    for relative_path in MODEL_PROVENANCE_FILES:
        _validate_model_provenance(evaluation_root / relative_path)
        model_provenance_count += 1

    label_mapping_count = 0
    for relative_path in LABEL_MAPPING_FILES:
        _validate_label_mapping(evaluation_root / relative_path)
        label_mapping_count += 1

    return ValidationSummary(
        files_checked=len(REQUIRED_FILES),
        json_outputs_checked=len(OUTPUT_FILES),
        fixture_results_checked=fixture_result_count,
        model_provenance_checked=model_provenance_count,
        label_mapping_checked=label_mapping_count,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Roadmap 4.3 lightweight evaluation example artifacts.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="genre-classifier service root. Defaults to the current working directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = validate_all(args.root)
    except ValidationError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "validation ok: "
        f"files={summary.files_checked}, "
        f"json_outputs={summary.json_outputs_checked}, "
        f"fixture_results={summary.fixture_results_checked}, "
        f"model_provenance={summary.model_provenance_checked}, "
        f"label_mapping={summary.label_mapping_checked}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
