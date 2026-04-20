import json
from pathlib import Path

from app.evaluation import (
    load_roadmap_2_9_subset_manifest,
    run_roadmap_2_9_offline_evaluation,
)


FIXTURE_BUNDLE_PATH = Path("evaluation/fixtures/roadmap_2_9/sample_comparison_inputs.json")


def test_load_roadmap_2_9_subset_manifest_reads_curated_subset():
    subset_manifest = load_roadmap_2_9_subset_manifest("curated")

    assert subset_manifest == {
        "manifest_version": "roadmap-2.9-curated-subset-v1",
        "roadmap_stage": "2.9",
        "subset_name": "curated",
        "source_manifest": "samples.master.json",
        "sample_ids": [
            "curated_baseline_001",
            "curated_golden_001",
            "curated_repeat_001",
            "curated_golden_repeat_001",
        ],
    }


def test_run_roadmap_2_9_offline_evaluation_aggregates_curated_subset():
    result = run_roadmap_2_9_offline_evaluation(
        subset_name="curated",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    assert result["roadmap_stage"] == "2.9"
    assert result["subset_name"] == "curated"
    assert result["source_manifest"] == "samples.master.json"
    assert result["evaluated_sample_count"] == 4
    assert result["evaluated_sample_ids"] == [
        "curated_baseline_001",
        "curated_golden_001",
        "curated_repeat_001",
        "curated_golden_repeat_001",
    ]
    assert result["missing_sample_ids"] == []
    assert result["warning_case_counts"] == {
        "llm_empty_output": 1,
        "llm_partial_output": 1,
        "llm_weak_top_score": 1,
        "no_shared_tags": 1,
    }
    assert result["samples_with_warnings"] == [
        "curated_golden_001",
        "curated_repeat_001",
        "curated_golden_repeat_001",
    ]
    assert [item["sample_id"] for item in result["per_sample_results"]] == [
        "curated_baseline_001",
        "curated_golden_001",
        "curated_repeat_001",
        "curated_golden_repeat_001",
    ]
    assert result["per_sample_results"][0]["warning_cases"] == []
    assert result["per_sample_results"][1]["warning_cases"] == [
        "llm_partial_output",
        "llm_weak_top_score",
    ]
    assert result["per_sample_results"][2]["warning_cases"] == [
        "llm_empty_output",
    ]
    assert result["per_sample_results"][3]["warning_cases"] == [
        "no_shared_tags",
    ]


def test_run_roadmap_2_9_offline_evaluation_handles_missing_sample_inputs(tmp_path):
    original_bundle = json.loads(FIXTURE_BUNDLE_PATH.read_text(encoding="utf-8"))
    partial_bundle = {
        "roadmap_stage": original_bundle["roadmap_stage"],
        "samples": [
            item
            for item in original_bundle["samples"]
            if item["sample_id"] != "curated_repeat_001"
        ],
    }
    partial_bundle_path = tmp_path / "partial_bundle.json"
    partial_bundle_path.write_text(json.dumps(partial_bundle, indent=2), encoding="utf-8")

    result = run_roadmap_2_9_offline_evaluation(
        subset_name="curated",
        comparison_input_path=partial_bundle_path,
    )

    assert result["evaluated_sample_count"] == 3
    assert result["evaluated_sample_ids"] == [
        "curated_baseline_001",
        "curated_golden_001",
        "curated_golden_repeat_001",
    ]
    assert result["missing_sample_ids"] == ["curated_repeat_001"]
    assert [item["sample_id"] for item in result["per_sample_results"]] == [
        "curated_baseline_001",
        "curated_golden_001",
        "curated_golden_repeat_001",
    ]


def test_run_roadmap_2_9_offline_evaluation_returns_deterministic_repeat_run_shape():
    result = run_roadmap_2_9_offline_evaluation(
        subset_name="repeat_run",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    assert result == {
        "roadmap_stage": "2.9",
        "subset_name": "repeat_run",
        "source_manifest": "samples.master.json",
        "evaluated_sample_count": 2,
        "evaluated_sample_ids": [
            "curated_repeat_001",
            "curated_golden_repeat_001",
        ],
        "missing_sample_ids": [],
        "warning_case_counts": {
            "llm_empty_output": 1,
            "no_shared_tags": 1,
        },
        "samples_with_warnings": [
            "curated_repeat_001",
            "curated_golden_repeat_001",
        ],
        "per_sample_results": [
            {
                "sample_id": "curated_repeat_001",
                "input_ref": "fixtures/eval/placeholders/curated_repeat_001.audio",
                "notes": "Placeholder for a repeat-run stability check sample.",
                "risk_category": "stability_drift",
                "legacy_provider_name": "legacy_musicnn",
                "llm_provider_name": "llm",
                "legacy_model_name": "legacy-offline",
                "llm_model_name": "llm-offline",
                "legacy_tags": ["house"],
                "llm_tags": [],
                "shared_tags": [],
                "legacy_only_tags": ["house"],
                "llm_only_tags": [],
                "overlap_summary": {
                    "legacy_tag_count": 1,
                    "llm_tag_count": 0,
                    "shared_tag_count": 0,
                    "legacy_only_tag_count": 1,
                    "llm_only_tag_count": 0,
                    "overlap_ratio_vs_legacy": 0.0,
                    "overlap_ratio_vs_llm": 0.0,
                    "jaccard_similarity": 0.0,
                },
                "ranking_drift": [],
                "warning_flags": {
                    "legacy_empty_output": False,
                    "llm_empty_output": True,
                    "legacy_partial_output": False,
                    "llm_partial_output": False,
                    "llm_weak_top_score": False,
                    "no_shared_tags": False,
                },
                "warning_cases": ["llm_empty_output"],
            },
            {
                "sample_id": "curated_golden_repeat_001",
                "input_ref": "fixtures/eval/placeholders/curated_golden_repeat_001.audio",
                "notes": "Placeholder for a sample that participates in both strict regression checks and repeat-run comparisons.",
                "risk_category": "ambiguous_boundary",
                "legacy_provider_name": "legacy_musicnn",
                "llm_provider_name": "llm",
                "legacy_model_name": "legacy-offline",
                "llm_model_name": "llm-offline",
                "legacy_tags": ["shoegaze", "dream pop"],
                "llm_tags": ["drum and bass", "breakbeat"],
                "shared_tags": [],
                "legacy_only_tags": ["shoegaze", "dream pop"],
                "llm_only_tags": ["drum and bass", "breakbeat"],
                "overlap_summary": {
                    "legacy_tag_count": 2,
                    "llm_tag_count": 2,
                    "shared_tag_count": 0,
                    "legacy_only_tag_count": 2,
                    "llm_only_tag_count": 2,
                    "overlap_ratio_vs_legacy": 0.0,
                    "overlap_ratio_vs_llm": 0.0,
                    "jaccard_similarity": 0.0,
                },
                "ranking_drift": [],
                "warning_flags": {
                    "legacy_empty_output": False,
                    "llm_empty_output": False,
                    "legacy_partial_output": False,
                    "llm_partial_output": False,
                    "llm_weak_top_score": False,
                    "no_shared_tags": True,
                },
                "warning_cases": ["no_shared_tags"],
            },
        ],
    }
