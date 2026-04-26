import json
from pathlib import Path

from app.evaluation import (
    ROADMAP_2_11_CURATED_REVIEW_ARTIFACT_VERSION,
    build_roadmap_2_11_curated_review_artifact,
    run_roadmap_2_10_offline_evaluation,
)
from app.evaluation.run_roadmap_2_9 import main


FIXTURE_BUNDLE_PATH = Path("evaluation/fixtures/roadmap_2_9/sample_comparison_inputs.json")
COMMITTED_ARTIFACT_PATH = Path("evaluation/artifacts/roadmap_2_11/curated_review_v1.json")


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

    assert artifact["candidate_evidence_summary"]["automatic_candidate_generation"] == "disabled"
    assert artifact["candidate_evidence_summary"]["candidate_count"] == 0
    assert "candidates" not in artifact


def test_roadmap_2_11_curated_review_artifact_preserves_empty_llm_evidence():
    evaluation_result = run_roadmap_2_10_offline_evaluation(
        subset_name="curated_v1",
        comparison_input_path=FIXTURE_BUNDLE_PATH,
    )

    artifact = build_roadmap_2_11_curated_review_artifact(evaluation_result)

    empty_output_item = next(
        item
        for item in artifact["per_item_results"]
        if item["sample_id"] == "curated_repeat_001"
    )

    assert empty_output_item["legacy_tags"] == ["house"]
    assert empty_output_item["llm_tags"] == []
    assert empty_output_item["warning_cases"] == ["llm_empty_output"]
    assert artifact["warning_rollups"]["warning_case_counts"]["llm_empty_output"] == 1
    assert {
        "sample_id": "curated_repeat_001",
        "category": "ranking_stability",
        "reasons": ["warnings"],
        "warning_cases": ["llm_empty_output"],
    } in artifact["review_queue"]
    assert artifact["readiness_buckets"]["current"]["bucket"] == "not-ready"
    assert "blocking warning cases: llm_empty_output, no_shared_tags" in artifact[
        "readiness_buckets"
    ]["decision_summary"]["blocking_findings"]
    assert artifact["candidate_evidence_summary"]["empty_llm_output_sample_ids"] == [
        "curated_repeat_001"
    ]
    assert artifact["candidate_evidence_summary"]["empty_llm_output_blocks_readiness"] is True
    assert artifact["candidate_evidence_summary"]["warning_case_counts"][
        "llm_empty_output"
    ] == 1


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


def test_committed_roadmap_2_11_curated_review_artifact_has_review_shape():
    artifact = json.loads(COMMITTED_ARTIFACT_PATH.read_text(encoding="utf-8"))

    assert artifact["artifact_version"] == ROADMAP_2_11_CURATED_REVIEW_ARTIFACT_VERSION
    assert artifact["roadmap"] == "2.11"
    assert artifact["stage"] == "curated_findings_review"
    assert artifact["source_roadmap_stage"] == "2.10"
    assert artifact["subset_name"] == "curated_v1"
    assert artifact["source_manifests"]["manifest_path"] == (
        "evaluation/manifests/roadmap_2_10/curated_v1.json"
    )
    assert isinstance(artifact["reviewed_items"], list)
    assert artifact["reviewed_items"]
    assert isinstance(artifact["per_item_results"], list)
    assert isinstance(artifact["category_summaries"], list)
    assert isinstance(artifact["warning_rollups"], dict)
    assert isinstance(artifact["review_queue"], list)
    assert artifact["readiness_buckets"]["allowed"] == [
        "ready",
        "limited-ready",
        "not-ready",
    ]
    assert artifact["candidate_evidence_summary"]["automatic_candidate_generation"] == "disabled"
    assert artifact["candidate_evidence_summary"]["candidate_count"] == 0
    assert artifact["candidate_evidence_summary"]["empty_llm_output_sample_ids"] == [
        "curated_repeat_001"
    ]
    assert "candidates" not in artifact
