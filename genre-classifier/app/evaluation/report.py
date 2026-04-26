ROADMAP_2_9_EVALUATION_REPORT_VERSION = "roadmap-2.9-evaluation-report-v1"
ROADMAP_2_11_CURATED_REVIEW_ARTIFACT_VERSION = "roadmap-2.11-curated-review-v1"


def build_roadmap_2_9_evaluation_report(evaluation_result):
    report = {
        "report_version": ROADMAP_2_9_EVALUATION_REPORT_VERSION,
        "roadmap_stage": evaluation_result.get("roadmap_stage"),
        "subset_name": evaluation_result.get("subset_name"),
        "source_manifest": evaluation_result.get("source_manifest"),
        "run_summary": {
            "evaluated_sample_count": evaluation_result.get("evaluated_sample_count", 0),
            "evaluated_sample_ids": list(evaluation_result.get("evaluated_sample_ids", [])),
            "missing_sample_ids": list(evaluation_result.get("missing_sample_ids", [])),
        },
        "warning_summary": {
            "warning_case_counts": {
                key: evaluation_result.get("warning_case_counts", {}).get(key)
                for key in sorted(evaluation_result.get("warning_case_counts", {}))
            },
            "samples_with_warnings": list(evaluation_result.get("samples_with_warnings", [])),
        },
        "per_sample_results": list(evaluation_result.get("per_sample_results", [])),
    }

    manifest_metadata = {
        key: evaluation_result.get(key)
        for key in ("manifest_version", "manifest_path", "manifest_sample_count")
        if key in evaluation_result
    }
    if manifest_metadata:
        report["manifest_metadata"] = manifest_metadata

    for report_key in (
        "category_summary",
        "warning_rollups",
        "review_queue",
        "readiness",
        "decision_summary",
    ):
        if report_key in evaluation_result:
            report[report_key] = evaluation_result.get(report_key)

    return report


def build_roadmap_2_11_curated_review_artifact(evaluation_result):
    per_item_results = list(evaluation_result.get("per_sample_results", []))
    review_queue = list(evaluation_result.get("review_queue", []))
    readiness = evaluation_result.get("readiness", {})
    decision_summary = evaluation_result.get("decision_summary") or {}
    warning_case_counts = {
        key: evaluation_result.get("warning_case_counts", {}).get(key)
        for key in sorted(evaluation_result.get("warning_case_counts", {}))
    }
    empty_llm_output_sample_ids = [
        item.get("sample_id")
        for item in per_item_results
        if "llm_empty_output" in item.get("warning_cases", [])
    ]

    return {
        "artifact_version": ROADMAP_2_11_CURATED_REVIEW_ARTIFACT_VERSION,
        "roadmap": "2.11",
        "stage": "curated_findings_review",
        "source_roadmap_stage": evaluation_result.get("roadmap_stage"),
        "subset_name": evaluation_result.get("subset_name"),
        "source_manifests": {
            key: evaluation_result.get(key)
            for key in (
                "manifest_version",
                "manifest_path",
                "source_manifest",
                "manifest_sample_count",
            )
            if key in evaluation_result
        },
        "reviewed_items": [
            {
                "sample_id": item.get("sample_id"),
                "category": item.get("category"),
                "difficulty": item.get("difficulty"),
                "warning_cases": list(item.get("warning_cases", [])),
                "review_required": bool(item.get("warning_cases")),
            }
            for item in per_item_results
        ],
        "per_item_results": per_item_results,
        "category_summaries": list(evaluation_result.get("category_summary", [])),
        "warning_rollups": evaluation_result.get(
            "warning_rollups",
            {
                "warning_case_counts": dict(evaluation_result.get("warning_case_counts", {})),
                "warning_sample_ids": list(evaluation_result.get("samples_with_warnings", [])),
                "warning_samples": [],
            },
        ),
        "review_queue": review_queue,
        "readiness_buckets": {
            "allowed": ["ready", "limited-ready", "not-ready"],
            "current": readiness,
            "decision_summary": decision_summary,
        },
        "candidate_evidence_summary": {
            "automatic_candidate_generation": "disabled",
            "candidate_count": 0,
            "warning_case_counts": warning_case_counts,
            "review_queue_sample_ids": [
                item.get("sample_id")
                for item in review_queue
                if item.get("sample_id")
            ],
            "blocking_findings": list(decision_summary.get("blocking_findings", [])),
            "empty_llm_output_sample_ids": empty_llm_output_sample_ids,
            "empty_llm_output_blocks_readiness": bool(
                empty_llm_output_sample_ids and readiness.get("bucket") != "ready"
            ),
            "notes": [
                "This artifact records review evidence only.",
                "Fix candidates must be selected in evaluation/manifests/roadmap_2_11/fix_candidates_v1.json after human review.",
            ],
        },
    }
