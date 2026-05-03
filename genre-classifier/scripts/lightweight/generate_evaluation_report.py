#!/usr/bin/env python3
"""Generate an offline-only lightweight evaluation markdown report.

The generator compares existing static JSON output artifacts. It does not run
inference, call /classify, import production provider/runtime modules, load
models, process audio, or use the network.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WARNING_CATEGORIES = (
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

RESOURCE_METRIC_KEYS = (
    "mean_latency_ms",
    "p95_latency_ms",
    "peak_memory_mb",
    "startup_import_time_ms",
    "model_size_mb",
    "dependency_runtime_weight_mb",
    "docker_image_size_impact_mb",
)


class ReportGenerationError(Exception):
    """Raised for controlled CLI failures."""


@dataclass(frozen=True)
class FixtureComparison:
    fixture_id: str
    baseline_tags: list[str]
    candidate_tags: list[str]
    top1_overlap: int
    top3_overlap: int
    top5_overlap: int
    top1_ratio: float
    top3_ratio: float
    top5_ratio: float
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class AggregateComparison:
    fixture_count: int
    compared_fixture_count: int
    baseline_tag_count: int
    candidate_tag_count: int
    overlap_count: int
    overlap_ratio: float
    average_top1_ratio: float
    average_top3_ratio: float
    average_top5_ratio: float


def _load_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportGenerationError(f"Unable to read JSON input {path}: {exc}") from exc

    if not text.strip():
        raise ReportGenerationError(f"JSON input is empty: {path}")

    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReportGenerationError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(value, dict):
        raise ReportGenerationError(f"JSON input must be an object: {path}")
    return value


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportGenerationError(f"Unable to read manifest {path}: {exc}") from exc


def _as_text(value: Any, default: str = "unknown") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _fixture_results(data: dict[str, Any]) -> list[dict[str, Any]]:
    results = data.get("fixture_results")
    if isinstance(results, list):
        return [item for item in results if isinstance(item, dict)]
    return [data]


def _fixture_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for index, result in enumerate(_fixture_results(data), start=1):
        fixture_id = _as_text(result.get("fixture_id"), f"fixture_{index}")
        mapped[fixture_id] = result
    return mapped


def _genre_tags(result: dict[str, Any]) -> list[str]:
    genres = result.get("genres")
    if not isinstance(genres, list):
        return []

    tags: list[str] = []
    seen: set[str] = set()
    for item in genres:
        if not isinstance(item, dict):
            continue
        tag = item.get("tag")
        if not isinstance(tag, str) or not tag.strip():
            continue
        normalized = tag.strip().casefold()
        if normalized not in seen:
            seen.add(normalized)
            tags.append(tag.strip())
    return tags


def _normalized_genres(result: dict[str, Any]) -> list[str]:
    values = result.get("normalized_genres")
    if not isinstance(values, list):
        return []
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


def _top_n_overlap(baseline_tags: list[str], candidate_tags: list[str], n: int) -> tuple[int, float]:
    baseline = {tag.casefold() for tag in baseline_tags[:n]}
    candidate = {tag.casefold() for tag in candidate_tags[:n]}
    denominator = max(len(baseline), len(candidate))
    overlap = len(baseline & candidate)
    return overlap, overlap / denominator if denominator else 0.0


def _compare_fixtures(baseline: dict[str, Any], candidate: dict[str, Any]) -> list[FixtureComparison]:
    baseline_by_id = _fixture_map(baseline)
    candidate_by_id = _fixture_map(candidate)
    fixture_ids = sorted(set(baseline_by_id) | set(candidate_by_id))
    comparisons: list[FixtureComparison] = []

    for fixture_id in fixture_ids:
        baseline_result = baseline_by_id.get(fixture_id, {})
        candidate_result = candidate_by_id.get(fixture_id, {})
        baseline_tags = _genre_tags(baseline_result)
        candidate_tags = _genre_tags(candidate_result)
        top1_overlap, top1_ratio = _top_n_overlap(baseline_tags, candidate_tags, 1)
        top3_overlap, top3_ratio = _top_n_overlap(baseline_tags, candidate_tags, 3)
        top5_overlap, top5_ratio = _top_n_overlap(baseline_tags, candidate_tags, 5)

        warnings: list[str] = []
        if fixture_id not in baseline_by_id or fixture_id not in candidate_by_id:
            warnings.append("comparison_incomplete")
        if not baseline_tags or not candidate_tags:
            warnings.append("empty_output")
        if baseline_result.get("ok") is False:
            warnings.append("baseline_failed")
        if candidate_result.get("ok") is False:
            warnings.append("candidate_failed")

        comparisons.append(
            FixtureComparison(
                fixture_id=fixture_id,
                baseline_tags=baseline_tags,
                candidate_tags=candidate_tags,
                top1_overlap=top1_overlap,
                top3_overlap=top3_overlap,
                top5_overlap=top5_overlap,
                top1_ratio=top1_ratio,
                top3_ratio=top3_ratio,
                top5_ratio=top5_ratio,
                warnings=tuple(dict.fromkeys(warnings)),
            )
        )

    return comparisons


def _aggregate(comparisons: list[FixtureComparison]) -> AggregateComparison:
    baseline_tags: set[str] = set()
    candidate_tags: set[str] = set()
    for comparison in comparisons:
        baseline_tags.update(tag.casefold() for tag in comparison.baseline_tags)
        candidate_tags.update(tag.casefold() for tag in comparison.candidate_tags)

    denominator = max(len(baseline_tags), len(candidate_tags))
    overlap_count = len(baseline_tags & candidate_tags)
    compared = [item for item in comparisons if item.baseline_tags and item.candidate_tags]

    def average(field: str) -> float:
        if not compared:
            return 0.0
        return sum(getattr(item, field) for item in compared) / len(compared)

    return AggregateComparison(
        fixture_count=len(comparisons),
        compared_fixture_count=len(compared),
        baseline_tag_count=len(baseline_tags),
        candidate_tag_count=len(candidate_tags),
        overlap_count=overlap_count,
        overlap_ratio=overlap_count / denominator if denominator else 0.0,
        average_top1_ratio=average("top1_ratio"),
        average_top3_ratio=average("top3_ratio"),
        average_top5_ratio=average("top5_ratio"),
    )


def _artifact_warnings(*artifacts: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for artifact in artifacts:
        raw = artifact.get("warnings")
        if not isinstance(raw, list):
            continue
        for item in raw:
            if isinstance(item, str):
                warnings.append(item)
            elif isinstance(item, dict) and isinstance(item.get("category"), str):
                warnings.append(item["category"])
    return warnings


def _resource_missing(data: dict[str, Any]) -> bool:
    metrics = data.get("aggregate_metrics")
    if not isinstance(metrics, dict):
        return True
    return any(metrics.get(key) is None for key in RESOURCE_METRIC_KEYS)


def _candidate_license_unknown(candidate: dict[str, Any]) -> bool:
    model = candidate.get("model")
    if not isinstance(model, dict):
        return True
    license_value = str(model.get("license", "")).strip().casefold()
    return license_value in {"", "unknown", "not-evaluated", "not evaluated", "example-only"}


def _candidate_provenance_unknown(candidate: dict[str, Any]) -> bool:
    model = candidate.get("model")
    if not isinstance(model, dict):
        return True
    provenance = str(model.get("provenance_note", "")).strip().casefold()
    source = str(model.get("model_source", "")).strip().casefold()
    return not provenance or "placeholder" in provenance or not source or "not-used" in source


def _collect_warning_categories(
    baseline: dict[str, Any], candidate: dict[str, Any], comparisons: list[FixtureComparison]
) -> list[str]:
    categories = set(_artifact_warnings(baseline, candidate))
    for comparison in comparisons:
        categories.update(comparison.warnings)
    if _resource_missing(baseline) or _resource_missing(candidate):
        categories.add("runtime_metric_missing")
    if _candidate_license_unknown(candidate):
        categories.add("license_unknown")
    if _candidate_provenance_unknown(candidate):
        categories.add("model_provenance_unknown")
    if any(not item.baseline_tags or not item.candidate_tags for item in comparisons):
        categories.add("comparison_incomplete")
    return sorted(categories)


def _manifest_metadata(text: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for key in ("schema_version", "artifact_type", "manifest_id", "baseline_provider"):
        match = re.search(rf'^{re.escape(key)}:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
        if match:
            metadata[key] = match.group(1).strip()
    metadata["fixture_count"] = len(re.findall(r"^\s*-\s+id:\s*", text, re.MULTILINE))
    metadata["categories"] = sorted(set(re.findall(r'category:\s*"([^"]+)"', text)))
    return metadata


def _format_ratio(value: float) -> str:
    return f"{value:.3f}"


def _format_list(values: list[str] | tuple[str, ...]) -> str:
    return ", ".join(values) if values else "none"


def _table_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _top_n_fraction(comparison: FixtureComparison, n: int, overlap: int) -> str:
    denominator = max(len(comparison.baseline_tags[:n]), len(comparison.candidate_tags[:n]))
    return f"{overlap}/{denominator}" if denominator else "0/0"


def generate_report(
    baseline_path: Path,
    candidate_path: Path,
    manifest_path: Path,
    candidate_name: str | None,
    decision: str,
) -> str:
    baseline = _load_json(baseline_path)
    candidate = _load_json(candidate_path)
    manifest_text = _read_text(manifest_path)
    manifest = _manifest_metadata(manifest_text)
    comparisons = _compare_fixtures(baseline, candidate)
    aggregate = _aggregate(comparisons)
    warning_categories = _collect_warning_categories(baseline, candidate, comparisons)

    baseline_provider = _as_text(baseline.get("baseline_provider") or baseline.get("provider"), "legacy_musicnn")
    candidate_provider = candidate_name or _as_text(candidate.get("provider"), "unknown_candidate")
    controlled_hits = sum(1 for item in comparisons if _normalized_genres(_fixture_map(candidate).get(item.fixture_id, {})))

    lines = [
        "# Roadmap 4.13 ONNX Candidate Offline Evaluation Report",
        "",
        "Status: offline-only static artifact comparison; not production decision.",
        "",
        "## Summary",
        "",
        "This report compares existing static baseline and candidate JSON output artifacts. It does not run inference, call `/classify`, import production provider/runtime modules, load models, process audio, or use the network.",
        "",
        "Required markers:",
        "",
        "- offline-only static artifact comparison",
        "- not production decision",
        "- inference executed: no",
        "- /classify called: no",
        "- production provider/runtime imports: no",
        "- default provider changed: no",
        "- approval gate: not approved for production",
        "",
        "Synthetic/example artifacts, when used, are documentation evidence only and must not be treated as real quality evaluation.",
        "",
        "## Scope",
        "",
        "Roadmap 4.13 scope is limited to report generation from already captured artifacts. Production runtime, provider factory wiring, default provider selection, `/classify`, Docker, dependencies, model files, and audio fixtures are out of scope.",
        "",
        "## Production Contract",
        "",
        "`legacy_musicnn` remains the production baseline and default provider.",
        "",
        "The `/classify` contract is unchanged. Provider output examples preserve:",
        "",
        "- `ok`",
        "- `message`",
        "- `genres`",
        "- `genres_pretty`",
        "",
        "## Baseline Provider",
        "",
        f"Baseline provider: `{baseline_provider}`.",
        f"Baseline output artifact: `{baseline_path}`.",
        "",
        "## Candidate Provider",
        "",
        f"Candidate provider: `{candidate_provider}`.",
        f"Candidate output artifact: `{candidate_path}`.",
        "",
        "## Manifest",
        "",
        f"Manifest: `{manifest_path}`.",
        "",
        f"- schema_version: `{manifest.get('schema_version', 'unknown')}`",
        f"- artifact_type: `{manifest.get('artifact_type', 'unknown')}`",
        f"- manifest_id: `{manifest.get('manifest_id', 'unknown')}`",
        f"- shallow fixture count: `{manifest.get('fixture_count', 0)}`",
        "",
        "## Fixture Coverage",
        "",
        f"Compared fixture rows: `{aggregate.fixture_count}`.",
        f"Rows with non-empty baseline and candidate genres: `{aggregate.compared_fixture_count}`.",
        "",
        "Manifest categories:",
        "",
    ]

    categories = manifest.get("categories")
    if isinstance(categories, list) and categories:
        lines.extend(f"- `{category}`" for category in categories)
    else:
        lines.append("- none detected from shallow manifest scan")

    lines.extend(
        [
            "",
            "## Aggregate Comparison",
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| baseline unique genre tags | {aggregate.baseline_tag_count} |",
            f"| candidate unique genre tags | {aggregate.candidate_tag_count} |",
            f"| unique tag overlap count | {aggregate.overlap_count} |",
            f"| unique tag overlap ratio | {_format_ratio(aggregate.overlap_ratio)} |",
            f"| average top-1 overlap ratio | {_format_ratio(aggregate.average_top1_ratio)} |",
            f"| average top-3 overlap ratio | {_format_ratio(aggregate.average_top3_ratio)} |",
            f"| average top-5 overlap ratio | {_format_ratio(aggregate.average_top5_ratio)} |",
            "",
            "## Controlled Vocabulary Results",
            "",
            f"Candidate rows with `normalized_genres`: `{controlled_hits}` of `{aggregate.fixture_count}`.",
            "Controlled vocabulary compatibility is inferred only from existing artifact fields; no mapping, model output interpretation, or inference is performed by this generator.",
            "",
            "## OOV Results",
            "",
            "OOV quality is not measured by this static generator. Existing artifact warning categories are preserved below. Missing explicit OOV evidence should be reviewed as `comparison_incomplete` when production-quality evaluation is requested.",
            "",
            "## Top-N Overlap",
            "",
            "Top-N overlap uses available ordered `genres[].tag` values from the static artifacts.",
            "",
            "| Scope | Top-1 | Top-3 | Top-5 |",
            "| --- | --- | --- | --- |",
            f"| average ratio | {_format_ratio(aggregate.average_top1_ratio)} | {_format_ratio(aggregate.average_top3_ratio)} | {_format_ratio(aggregate.average_top5_ratio)} |",
            "",
            "## Resource Metrics",
            "",
            "Resource metrics are copied from artifact metadata when present. Missing or null resource fields are reported as `runtime_metric_missing`; the generator does not measure runtime behavior.",
            "",
            "| Artifact | mean_latency_ms | p95_latency_ms | peak_memory_mb | startup_import_time_ms | model_size_mb | dependency_runtime_weight_mb | docker_image_size_impact_mb |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            _resource_row("baseline", baseline),
            _resource_row("candidate", candidate),
            "",
            "## Failures and Warnings",
            "",
            "Observed warning categories:",
            "",
        ]
    )

    if warning_categories:
        lines.extend(f"- `{category}`" for category in warning_categories)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Known warning categories for Roadmap 4.5 compatibility:",
            "",
        ]
    )
    lines.extend(f"- `{category}`" for category in WARNING_CATEGORIES)
    lines.extend(
        [
            "",
            "## Known Gaps",
            "",
            "- no inference was executed by this generator",
            "- no `/classify` call was made",
            "- no production provider/runtime import was made",
            "- candidate model provenance and license remain review items unless supplied by separate approved artifacts",
            "- synthetic/example artifacts are not real quality evaluation",
            "- resource metrics may be absent or illustrative",
            "",
            "## Decision",
            "",
            decision,
            "",
            "This report is not approval for provider implementation, shadow execution, canary rollout, default-provider switch, production migration, or production ONNX use.",
            "",
            "## Approval Gate Status",
            "",
            "| Gate | Status | Notes |",
            "| --- | --- | --- |",
            "| offline static report generation | complete | Roadmap 4.13 generator produced this report from static artifacts. |",
            "| provider implementation | not_approved | No production provider implementation is created or approved. |",
            "| shadow execution | not_approved | No shadow path is implemented or approved. |",
            "| canary rollout | not_approved | No traffic exposure is implemented or approved. |",
            "| default provider switch | not_approved | `legacy_musicnn` remains the default provider. |",
            "| production migration | not_approved | approval gate: not approved for production. |",
            "",
            "## Appendix: Per-Fixture Results",
            "",
            "| Fixture ID | Baseline tags | Candidate tags | Top-1 | Top-3 | Top-5 | Warnings |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for comparison in comparisons:
        lines.append(
            "| "
            + " | ".join(
                (
                    _table_cell(comparison.fixture_id),
                    _table_cell(_format_list(comparison.baseline_tags)),
                    _table_cell(_format_list(comparison.candidate_tags)),
                    _top_n_fraction(comparison, 1, comparison.top1_overlap),
                    _top_n_fraction(comparison, 3, comparison.top3_overlap),
                    _top_n_fraction(comparison, 5, comparison.top5_overlap),
                    _table_cell(_format_list(comparison.warnings)),
                )
            )
            + " |"
        )

    lines.append("")
    return "\n".join(lines)


def _resource_row(label: str, data: dict[str, Any]) -> str:
    metrics = data.get("aggregate_metrics")
    if not isinstance(metrics, dict):
        metrics = {}

    def value(key: str) -> str:
        raw = metrics.get(key)
        return "missing" if raw is None else str(raw)

    return (
        f"| {label} | {value('mean_latency_ms')} | {value('p95_latency_ms')} | "
        f"{value('peak_memory_mb')} | {value('startup_import_time_ms')} | "
        f"{value('model_size_mb')} | {value('dependency_runtime_weight_mb')} | "
        f"{value('docker_image_size_impact_mb')} |"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-output", required=True, type=Path)
    parser.add_argument("--candidate-output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    parser.add_argument("--candidate-name")
    parser.add_argument("--decision", default="no production decision")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = generate_report(
            baseline_path=args.baseline_output,
            candidate_path=args.candidate_output,
            manifest_path=args.manifest,
            candidate_name=args.candidate_name,
            decision=args.decision,
        )
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(report, encoding="utf-8")
    except ReportGenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: unable to write report {args.output_report}: {exc}", file=sys.stderr)
        return 2

    print(f"wrote report: {args.output_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
