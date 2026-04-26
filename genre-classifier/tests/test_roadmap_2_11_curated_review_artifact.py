import json
from pathlib import Path

from app.evaluation import (
    ROADMAP_2_11_CURATED_REVIEW_ARTIFACT_VERSION,
    build_roadmap_2_11_curated_review_artifact,
    run_roadmap_2_10_offline_evaluation,
)
from app.evaluation.run_roadmap_2_9 import main


FIXTURE_BUNDLE_PATH = Path("evaluation/fixtures/roadmap_2_9/sample_comparison_inputs.json")


def test_roadmap_2_11_curated_review_artifact_exposes_review_evidence_sections():
    evaluation_result = run_roadmap_2_10_offline_evaluation(
        subset_name="curated_v1",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    artifact = build_roadmap_2_11_curated_review_artifact(evaluation_result)

    assert artifact["artifact_version"] == ROADMAP_2_11_CURATED_REVIEW_ARTIFACT_VERSION
    assert artifact["roadmap"] == "2.11"
    assert artifact["stage"] == "curated_findings_review"
    assert artifact["source_roadmap_stage"] == "2.10"
    assert artifact["source_manifests"] == {
        "manifest_version": "roadmap-2.10-curated-v1",
        "manifest_path": "evaluation/manifests/roadmap_2_10/curated_v1.json",
        "source_manifest": "../roadmap_2_9/samples.master.json",
        "manifest_sample_count": 4,
    }
    assert [item["sample_id"] for item in artifact["reviewed_items"]] == [
        "curated_baseline_001",
        "curated_golden_001",
        "curated_repeat_001",
        "curated_golden_repeat_001",
    ]
    assert artifact["per_item_results"] == evaluation_result["per_sample_results"]


def test_roadmap_2_11_curated_review_artifact_preserves_rollups_and_queue():
    evaluation_result = run_roadmap_2_10_offline_evaluation(
        subset_name="curated_v1",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    artifact = build_roadmap_2_11_curated_review_artifact(evaluation_result)

    assert artifact["category_summaries"] == evaluation_result["category_summary"]
    assert artifact["warning_rollups"]["warning_case_counts"] == {
        "llm_empty_output": 1,
        "llm_partial_output": 1,
        "llm_weak_top_score": 1,
        "no_shared_tags": 1,
    }
    assert isinstance(artifact["review_queue"], list)
    assert artifact["review_queue"] == evaluation_result["review_queue"]


def test_roadmap_2_11_curated_review_artifact_keeps_readiness_buckets_reviewable():
    evaluation_result = run_roadmap_2_10_offline_evaluation(
        subset_name="curated_v1",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    artifact = build_roadmap_2_11_curated_review_artifact(evaluation_result)

    assert artifact["readiness_buckets"]["allowed"] == [
        "ready",
        "limited-ready",
        "not-ready",
    ]
    assert artifact["readiness_buckets"]["current"] == {
        "bucket": "not-ready",
        "reasons": [
            "blocking warning cases require review",
            "review queue is too large for next-step confidence",
        ],
    }


def test_roadmap_2_11_curated_review_artifact_does_not_generate_fix_candidates():
    evaluation_result = run_roadmap_2_10_offline_evaluation(
        subset_name="curated_v1",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    artifact = build_roadmap_2_11_curated_review_artifact(evaluation_result)

    assert artifact["candidate_evidence_summary"] == {
        "automatic_candidate_generation": "disabled",
        "candidate_count": 0,
        "notes": [
            "This artifact records review evidence only.",
            "Fix candidates must be selected in evaluation/manifests/roadmap_2_11/fix_candidates_v1.json after human review.",
        ],
    }
    assert "candidates" not in artifact


def test_roadmap_2_11_curated_review_entrypoint_writes_json_artifact(tmp_path):
    output_path = tmp_path / "evaluation" / "artifacts" / "roadmap_2_11" / "curated_review_v1.json"

    artifact = main(
        [
            "--roadmap-stage",
            "2.10",
            "--subset",
            "curated_v1",
            "--input-bundle",
            str(FIXTURE_BUNDLE_PATH),
            "--output-kind",
            "roadmap_2_11_curated_review",
            "--output",
            str(output_path),
        ]
    )

    written_artifact = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert written_artifact == artifact
    assert written_artifact["roadmap"] == "2.11"
