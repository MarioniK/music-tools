ROADMAP_2_9_EVALUATION_REPORT_VERSION = "roadmap-2.9-evaluation-report-v1"


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

    return report
