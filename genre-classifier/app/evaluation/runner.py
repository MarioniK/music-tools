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

    return {
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
