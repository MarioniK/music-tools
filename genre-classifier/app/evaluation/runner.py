import json
from pathlib import Path

from app.evaluation.comparison import compare_provider_results


REPO_ROOT = Path(__file__).resolve().parents[2]
ROADMAP_2_9_MANIFEST_DIR = REPO_ROOT / "evaluation" / "manifests" / "roadmap_2_9"
ROADMAP_2_10_MANIFEST_DIR = REPO_ROOT / "evaluation" / "manifests" / "roadmap_2_10"
ROADMAP_2_9_SUBSET_MANIFESTS = {
    "curated": "curated_samples.json",
    "golden": "golden_subset.json",
    "repeat_run": "repeat_run_subset.json",
}
ROADMAP_2_10_SUBSET_MANIFESTS = {
    "curated_v1": "curated_v1.json",
    "golden_v1": "golden_v1.json",
    "repeat_run_v1": "repeat_run_v1.json",
}
ROADMAP_2_10_BLOCKING_WARNING_CASES = {"llm_empty_output", "no_shared_tags"}


def load_roadmap_2_9_subset_manifest(
    subset_name: str,
    manifest_dir: Path = ROADMAP_2_9_MANIFEST_DIR,
):
    if subset_name not in ROADMAP_2_9_SUBSET_MANIFESTS:
        raise RuntimeError("unknown roadmap 2.9 subset")

    subset_manifest_path = Path(manifest_dir) / ROADMAP_2_9_SUBSET_MANIFESTS[subset_name]
    return _load_json_file(subset_manifest_path)


def load_roadmap_2_10_subset_manifest(
    subset_name: str,
    manifest_dir: Path = ROADMAP_2_10_MANIFEST_DIR,
):
    if subset_name not in ROADMAP_2_10_SUBSET_MANIFESTS:
        raise RuntimeError("unknown roadmap 2.10 subset")

    subset_manifest_path = Path(manifest_dir) / ROADMAP_2_10_SUBSET_MANIFESTS[subset_name]
    return _load_json_file(subset_manifest_path)


def run_roadmap_2_9_offline_evaluation(
    subset_name: str,
    comparison_input_path,
    manifest_dir: Path = ROADMAP_2_9_MANIFEST_DIR,
):
    manifest_dir = Path(manifest_dir)
    master_manifest = _load_json_file(manifest_dir / "samples.master.json")
    subset_manifest = load_roadmap_2_9_subset_manifest(subset_name=subset_name, manifest_dir=manifest_dir)
    comparison_bundle = _load_json_file(comparison_input_path)

    metadata_by_sample_id = {
        item["sample_id"]: item
        for item in master_manifest.get("samples", [])
        if isinstance(item, dict) and item.get("sample_id")
    }
    comparison_inputs_by_sample_id = {
        item["sample_id"]: item
        for item in comparison_bundle.get("samples", [])
        if isinstance(item, dict) and item.get("sample_id")
    }

    evaluated_sample_ids = []
    missing_sample_ids = []
    samples_with_warnings = []
    warning_case_counts = {}
    per_sample_results = []

    for sample_id in subset_manifest.get("sample_ids", []):
        if sample_id not in metadata_by_sample_id or sample_id not in comparison_inputs_by_sample_id:
            missing_sample_ids.append(sample_id)
            continue

        comparison_input = comparison_inputs_by_sample_id[sample_id]
        comparison_summary = compare_provider_results(
            legacy_result=comparison_input.get("legacy_result", {}),
            llm_result=comparison_input.get("llm_result", {}),
        )

        per_sample_result = {
            "sample_id": sample_id,
            "input_ref": metadata_by_sample_id[sample_id].get("input_ref"),
            "notes": metadata_by_sample_id[sample_id].get("notes"),
            "risk_category": metadata_by_sample_id[sample_id].get("risk_category"),
            **comparison_summary,
        }

        evaluated_sample_ids.append(sample_id)
        per_sample_results.append(per_sample_result)

        if comparison_summary["warning_cases"]:
            samples_with_warnings.append(sample_id)

        for warning_case in comparison_summary["warning_cases"]:
            warning_case_counts[warning_case] = warning_case_counts.get(warning_case, 0) + 1

    return {
        "roadmap_stage": master_manifest.get("roadmap_stage"),
        "subset_name": subset_manifest.get("subset_name"),
        "source_manifest": subset_manifest.get("source_manifest"),
        "evaluated_sample_count": len(evaluated_sample_ids),
        "evaluated_sample_ids": evaluated_sample_ids,
        "missing_sample_ids": missing_sample_ids,
        "warning_case_counts": {
            key: warning_case_counts[key]
            for key in sorted(warning_case_counts)
        },
        "samples_with_warnings": samples_with_warnings,
        "per_sample_results": per_sample_results,
    }


def run_roadmap_2_10_offline_evaluation(
    subset_name: str,
    comparison_input_path,
    manifest_dir: Path = ROADMAP_2_10_MANIFEST_DIR,
):
    manifest_dir = Path(manifest_dir)
    if subset_name not in ROADMAP_2_10_SUBSET_MANIFESTS:
        raise RuntimeError("unknown roadmap 2.10 subset")

    subset_manifest_path = manifest_dir / ROADMAP_2_10_SUBSET_MANIFESTS[subset_name]
    subset_manifest = load_roadmap_2_10_subset_manifest(
        subset_name=subset_name,
        manifest_dir=manifest_dir,
    )
    comparison_bundle = _load_json_file(comparison_input_path)

    comparison_inputs_by_sample_id = {
        item["sample_id"]: item
        for item in comparison_bundle.get("samples", [])
        if isinstance(item, dict) and item.get("sample_id")
    }

    evaluated_sample_ids = []
    missing_sample_ids = []
    samples_with_warnings = []
    warning_case_counts = {}
    warning_samples = []
    category_summaries = {}
    review_queue = []
    per_sample_results = []

    for entry in subset_manifest.get("entries", []):
        sample_id = entry.get("sample_id")
        category = entry.get("category")
        category_summary = _category_summary_for(category_summaries, category)
        category_summary["sample_count"] += 1

        if not sample_id or sample_id not in comparison_inputs_by_sample_id:
            missing_sample_ids.append(sample_id)
            category_summary["missing_sample_count"] += 1
            review_queue.append(
                {
                    "sample_id": sample_id,
                    "category": category,
                    "reasons": ["missing_sample"],
                    "warning_cases": [],
                }
            )
            continue

        comparison_input = comparison_inputs_by_sample_id[sample_id]
        comparison_summary = compare_provider_results(
            legacy_result=comparison_input.get("legacy_result", {}),
            llm_result=comparison_input.get("llm_result", {}),
        )

        per_sample_result = {
            "sample_id": sample_id,
            "subset": entry.get("subset"),
            "category": category,
            "difficulty": entry.get("difficulty"),
            "input_ref": entry.get("input_ref"),
            "notes": entry.get("notes"),
            **comparison_summary,
        }

        evaluated_sample_ids.append(sample_id)
        category_summary["evaluated_sample_count"] += 1
        per_sample_results.append(per_sample_result)

        if comparison_summary["warning_cases"]:
            samples_with_warnings.append(sample_id)
            warning_samples.append(
                {
                    "sample_id": sample_id,
                    "category": category,
                    "warning_cases": list(comparison_summary["warning_cases"]),
                }
            )
            category_summary["warning_sample_count"] += 1
            review_queue.append(
                {
                    "sample_id": sample_id,
                    "category": category,
                    "reasons": ["warnings"],
                    "warning_cases": list(comparison_summary["warning_cases"]),
                }
            )

        for warning_case in comparison_summary["warning_cases"]:
            warning_case_counts[warning_case] = warning_case_counts.get(warning_case, 0) + 1
            category_warning_counts = category_summary["warning_case_counts"]
            category_warning_counts[warning_case] = category_warning_counts.get(warning_case, 0) + 1

    result = {
        "roadmap_stage": subset_manifest.get("roadmap_stage"),
        "subset_name": subset_manifest.get("subset_name"),
        "manifest_version": subset_manifest.get("manifest_version"),
        "manifest_path": _repo_relative_path(subset_manifest_path),
        "source_manifest": subset_manifest.get("source_manifest"),
        "manifest_sample_count": len(subset_manifest.get("entries", [])),
        "evaluated_sample_count": len(evaluated_sample_ids),
        "evaluated_sample_ids": evaluated_sample_ids,
        "missing_sample_ids": missing_sample_ids,
        "warning_case_counts": {
            key: warning_case_counts[key]
            for key in sorted(warning_case_counts)
        },
        "samples_with_warnings": samples_with_warnings,
        "category_summary": _sorted_category_summaries(category_summaries),
        "warning_rollups": {
            "warning_case_counts": {
                key: warning_case_counts[key]
                for key in sorted(warning_case_counts)
            },
            "warning_sample_ids": list(samples_with_warnings),
            "warning_samples": warning_samples,
        },
        "review_queue": review_queue,
        "per_sample_results": per_sample_results,
    }
    readiness, decision_summary = build_roadmap_2_10_readiness_interpretation(result)
    result["readiness"] = readiness
    result["decision_summary"] = decision_summary
    return result


def _load_json_file(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _repo_relative_path(path):
    path = Path(path)
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _category_summary_for(category_summaries, category):
    if category not in category_summaries:
        category_summaries[category] = {
            "category": category,
            "sample_count": 0,
            "evaluated_sample_count": 0,
            "warning_sample_count": 0,
            "missing_sample_count": 0,
            "warning_case_counts": {},
        }
    return category_summaries[category]


def _sorted_category_summaries(category_summaries):
    summaries = []
    for category in sorted(category_summaries):
        summary = dict(category_summaries[category])
        summary["warning_case_counts"] = {
            key: summary["warning_case_counts"][key]
            for key in sorted(summary["warning_case_counts"])
        }
        summaries.append(summary)
    return summaries


def build_roadmap_2_10_readiness_interpretation(evaluation_result):
    missing_sample_ids = list(evaluation_result.get("missing_sample_ids", []))
    warning_case_counts = dict(evaluation_result.get("warning_case_counts", {}))
    review_queue = list(evaluation_result.get("review_queue", []))
    evaluated_sample_count = evaluation_result.get("evaluated_sample_count", 0)
    blocking_warning_cases = [
        warning_case
        for warning_case in sorted(warning_case_counts)
        if warning_case in ROADMAP_2_10_BLOCKING_WARNING_CASES
    ]
    review_queue_too_large = (
        evaluated_sample_count > 0
        and len(review_queue) > evaluated_sample_count / 2
    )

    blocking_findings = []
    reasons = []

    if missing_sample_ids:
        blocking_findings.append("missing_samples")
        reasons.append("missing sample inputs require review")

    if blocking_warning_cases:
        blocking_findings.append("blocking warning cases: {}".format(", ".join(blocking_warning_cases)))
        reasons.append("blocking warning cases require review")

    if review_queue_too_large:
        blocking_findings.append("review queue exceeds half of evaluated samples")
        reasons.append("review queue is too large for next-step confidence")

    if blocking_findings:
        bucket = "not-ready"
    elif review_queue or warning_case_counts:
        bucket = "limited-ready"
        reasons.append("non-blocking warnings require follow-up")
    else:
        bucket = "ready"
        reasons.append("artifacts are complete with no warnings or missing samples")

    follow_up_required = bucket != "ready"
    if bucket == "ready":
        summary = "Ready for the next safe offline evaluation or migration-preparation step; not a cutover approval."
    elif bucket == "limited-ready":
        summary = "Limited-ready because artifacts are complete but warning review is still required before broader migration planning."
    else:
        summary = "Not-ready because blocking findings must be resolved before the next roadmap step."

    return (
        {
            "bucket": bucket,
            "reasons": reasons,
        },
        {
            "bucket": bucket,
            "summary": summary,
            "blocking_findings": blocking_findings,
            "follow_up_required": follow_up_required,
            "next_step": "Resolve review queue findings before any broader migration step."
            if follow_up_required
            else "Continue only with the next safe offline evaluation or migration-preparation step.",
        },
    )
