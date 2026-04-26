from pathlib import Path

from app.evaluation import (
    ROADMAP_2_9_EVALUATION_REPORT_VERSION,
    build_roadmap_2_9_evaluation_report,
    run_roadmap_2_10_offline_evaluation,
    run_roadmap_2_9_offline_evaluation,
)
from app.evaluation.runner import build_roadmap_2_10_readiness_interpretation


FIXTURE_BUNDLE_PATH = Path("evaluation/fixtures/roadmap_2_9/sample_comparison_inputs.json")


def test_build_roadmap_2_9_evaluation_report_exposes_stable_top_level_sections():
    evaluation_result = run_roadmap_2_9_offline_evaluation(
        subset_name="curated",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    report = build_roadmap_2_9_evaluation_report(evaluation_result)

    assert report == {
        "report_version": ROADMAP_2_9_EVALUATION_REPORT_VERSION,
        "roadmap_stage": "2.9",
        "subset_name": "curated",
        "source_manifest": "samples.master.json",
        "run_summary": {
            "evaluated_sample_count": 4,
            "evaluated_sample_ids": [
                "curated_baseline_001",
                "curated_golden_001",
                "curated_repeat_001",
                "curated_golden_repeat_001",
            ],
            "missing_sample_ids": [],
        },
        "warning_summary": {
            "warning_case_counts": {
                "llm_empty_output": 1,
                "llm_partial_output": 1,
                "llm_weak_top_score": 1,
                "no_shared_tags": 1,
            },
            "samples_with_warnings": [
                "curated_golden_001",
                "curated_repeat_001",
                "curated_golden_repeat_001",
            ],
        },
        "per_sample_results": evaluation_result["per_sample_results"],
    }


def test_build_roadmap_2_9_evaluation_report_preserves_missing_samples_and_per_sample_results(tmp_path):
    partial_bundle_path = tmp_path / "partial_bundle.json"
    partial_bundle_path.write_text(
        """{
  "roadmap_stage": "2.9",
  "samples": [
    {
      "sample_id": "curated_baseline_001",
      "legacy_result": {
        "provider_name": "legacy_musicnn",
        "model_name": "legacy-offline",
        "genres": [{"tag": "indie rock", "score": 0.91}]
      },
      "llm_result": {
        "provider_name": "llm",
        "model_name": "llm-offline",
        "genres": [{"tag": "indie rock", "score": 0.88}]
      }
    }
  ]
}""",
        encoding="utf-8",
    )

    evaluation_result = run_roadmap_2_9_offline_evaluation(
        subset_name="golden",
        comparison_input_path=partial_bundle_path,
    )
    report = build_roadmap_2_9_evaluation_report(evaluation_result)

    assert report["report_version"] == ROADMAP_2_9_EVALUATION_REPORT_VERSION
    assert report["run_summary"]["evaluated_sample_count"] == 0
    assert report["run_summary"]["evaluated_sample_ids"] == []
    assert report["run_summary"]["missing_sample_ids"] == [
        "curated_golden_001",
        "curated_golden_repeat_001",
    ]
    assert report["warning_summary"]["warning_case_counts"] == {}
    assert report["warning_summary"]["samples_with_warnings"] == []
    assert report["per_sample_results"] == []


def test_build_roadmap_2_9_evaluation_report_keeps_repeat_run_sample_results_unchanged():
    evaluation_result = run_roadmap_2_9_offline_evaluation(
        subset_name="repeat_run",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    report = build_roadmap_2_9_evaluation_report(evaluation_result)

    assert [item["sample_id"] for item in report["per_sample_results"]] == [
        "curated_repeat_001",
        "curated_golden_repeat_001",
    ]
    assert report["per_sample_results"] == evaluation_result["per_sample_results"]


def test_build_roadmap_2_10_evaluation_report_includes_review_summaries():
    evaluation_result = run_roadmap_2_10_offline_evaluation(
        subset_name="curated_v1",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    report = build_roadmap_2_9_evaluation_report(evaluation_result)

    assert report["category_summary"] == [
        {
            "category": "clear_single_genre",
            "sample_count": 1,
            "evaluated_sample_count": 1,
            "warning_sample_count": 0,
            "missing_sample_count": 0,
            "warning_case_counts": {},
        },
        {
            "category": "contract_semantics",
            "sample_count": 1,
            "evaluated_sample_count": 1,
            "warning_sample_count": 1,
            "missing_sample_count": 0,
            "warning_case_counts": {
                "llm_partial_output": 1,
                "llm_weak_top_score": 1,
            },
        },
        {
            "category": "genre_boundary",
            "sample_count": 1,
            "evaluated_sample_count": 1,
            "warning_sample_count": 1,
            "missing_sample_count": 0,
            "warning_case_counts": {
                "no_shared_tags": 1,
            },
        },
        {
            "category": "ranking_stability",
            "sample_count": 1,
            "evaluated_sample_count": 1,
            "warning_sample_count": 1,
            "missing_sample_count": 0,
            "warning_case_counts": {
                "llm_empty_output": 1,
            },
        },
    ]
    assert report["warning_rollups"] == {
        "warning_case_counts": {
            "llm_empty_output": 1,
            "llm_partial_output": 1,
            "llm_weak_top_score": 1,
            "no_shared_tags": 1,
        },
        "warning_sample_ids": [
            "curated_golden_001",
            "curated_repeat_001",
            "curated_golden_repeat_001",
        ],
        "warning_samples": [
            {
                "sample_id": "curated_golden_001",
                "category": "contract_semantics",
                "warning_cases": ["llm_partial_output", "llm_weak_top_score"],
            },
            {
                "sample_id": "curated_repeat_001",
                "category": "ranking_stability",
                "warning_cases": ["llm_empty_output"],
            },
            {
                "sample_id": "curated_golden_repeat_001",
                "category": "genre_boundary",
                "warning_cases": ["no_shared_tags"],
            },
        ],
    }
    assert report["review_queue"] == [
        {
            "sample_id": "curated_golden_001",
            "category": "contract_semantics",
            "reasons": ["warnings"],
            "warning_cases": ["llm_partial_output", "llm_weak_top_score"],
        },
        {
            "sample_id": "curated_repeat_001",
            "category": "ranking_stability",
            "reasons": ["warnings"],
            "warning_cases": ["llm_empty_output"],
        },
        {
            "sample_id": "curated_golden_repeat_001",
            "category": "genre_boundary",
            "reasons": ["warnings"],
            "warning_cases": ["no_shared_tags"],
        },
    ]
    assert report["readiness"] == {
        "bucket": "not-ready",
        "reasons": [
            "blocking warning cases require review",
            "review queue is too large for next-step confidence",
        ],
    }
    assert report["decision_summary"] == {
        "bucket": "not-ready",
        "summary": "Not-ready because blocking findings must be resolved before the next roadmap step.",
        "blocking_findings": [
            "blocking warning cases: llm_empty_output, no_shared_tags",
            "review queue exceeds half of evaluated samples",
        ],
        "follow_up_required": True,
        "next_step": "Resolve review queue findings before any broader migration step.",
    }


def test_build_roadmap_2_10_evaluation_report_includes_missing_samples_in_review_queue(tmp_path):
    partial_bundle_path = tmp_path / "partial_bundle.json"
    partial_bundle_path.write_text(
        """{
  "roadmap_stage": "2.9",
  "samples": [
    {
      "sample_id": "curated_golden_repeat_001",
      "legacy_result": {
        "provider_name": "legacy_musicnn",
        "model_name": "legacy-offline",
        "genres": [{"tag": "shoegaze", "score": 0.9}]
      },
      "llm_result": {
        "provider_name": "llm",
        "model_name": "llm-offline",
        "genres": [{"tag": "breakbeat", "score": 0.9}]
      }
    }
  ]
}""",
        encoding="utf-8",
    )
    evaluation_result = run_roadmap_2_10_offline_evaluation(
        subset_name="golden_v1",
        comparison_input_path=partial_bundle_path,
    )

    report = build_roadmap_2_9_evaluation_report(evaluation_result)

    assert report["run_summary"]["missing_sample_ids"] == ["curated_golden_001"]
    assert report["category_summary"] == [
        {
            "category": "contract_semantics",
            "sample_count": 1,
            "evaluated_sample_count": 0,
            "warning_sample_count": 0,
            "missing_sample_count": 1,
            "warning_case_counts": {},
        },
        {
            "category": "genre_boundary",
            "sample_count": 1,
            "evaluated_sample_count": 1,
            "warning_sample_count": 1,
            "missing_sample_count": 0,
            "warning_case_counts": {
                "no_shared_tags": 1,
            },
        },
    ]
    assert report["review_queue"] == [
        {
            "sample_id": "curated_golden_001",
            "category": "contract_semantics",
            "reasons": ["missing_sample"],
            "warning_cases": [],
        },
        {
            "sample_id": "curated_golden_repeat_001",
            "category": "genre_boundary",
            "reasons": ["warnings"],
            "warning_cases": ["no_shared_tags"],
        },
    ]


def test_roadmap_2_10_readiness_interpretation_marks_clean_artifact_ready():
    readiness, decision_summary = build_roadmap_2_10_readiness_interpretation(
        {
            "evaluated_sample_count": 2,
            "missing_sample_ids": [],
            "warning_case_counts": {},
            "review_queue": [],
        }
    )

    assert readiness == {
        "bucket": "ready",
        "reasons": ["artifacts are complete with no warnings or missing samples"],
    }
    assert decision_summary == {
        "bucket": "ready",
        "summary": "Ready for the next safe offline evaluation or migration-preparation step; not a cutover approval.",
        "blocking_findings": [],
        "follow_up_required": False,
        "next_step": "Continue only with the next safe offline evaluation or migration-preparation step.",
    }


def test_roadmap_2_10_readiness_interpretation_marks_nonblocking_warnings_limited_ready():
    readiness, decision_summary = build_roadmap_2_10_readiness_interpretation(
        {
            "evaluated_sample_count": 4,
            "missing_sample_ids": [],
            "warning_case_counts": {
                "llm_partial_output": 1,
                "llm_weak_top_score": 1,
            },
            "review_queue": [
                {
                    "sample_id": "curated_golden_001",
                    "category": "contract_semantics",
                    "reasons": ["warnings"],
                    "warning_cases": ["llm_partial_output", "llm_weak_top_score"],
                }
            ],
        }
    )

    assert readiness == {
        "bucket": "limited-ready",
        "reasons": ["non-blocking warnings require follow-up"],
    }
    assert decision_summary == {
        "bucket": "limited-ready",
        "summary": "Limited-ready because artifacts are complete but warning review is still required before broader migration planning.",
        "blocking_findings": [],
        "follow_up_required": True,
        "next_step": "Resolve review queue findings before any broader migration step.",
    }
