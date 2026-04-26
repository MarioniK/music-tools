import json
from pathlib import Path

from app.evaluation import ROADMAP_2_9_EVALUATION_REPORT_VERSION
from app.evaluation.run_roadmap_2_9 import main


FIXTURE_BUNDLE_PATH = Path("evaluation/fixtures/roadmap_2_9/sample_comparison_inputs.json")


def test_roadmap_2_9_entrypoint_writes_json_report_file(tmp_path, capsys):
    output_path = tmp_path / "reports" / "curated_report.json"

    report = main(
        [
            "--subset",
            "curated",
            "--input-bundle",
            str(FIXTURE_BUNDLE_PATH),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    written_report = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert written_report["report_version"] == ROADMAP_2_9_EVALUATION_REPORT_VERSION
    assert written_report == report
    assert "subset=curated" in captured.out
    assert "evaluated_samples=4" in captured.out
    assert "missing_samples=0" in captured.out
    assert "warning_samples=3" in captured.out
    assert "output={}".format(output_path) in captured.out


def test_roadmap_2_9_entrypoint_passes_subset_through_to_report(tmp_path):
    output_path = tmp_path / "golden_report.json"

    report = main(
        [
            "--subset",
            "golden",
            "--input-bundle",
            str(FIXTURE_BUNDLE_PATH),
            "--output",
            str(output_path),
        ]
    )

    written_report = json.loads(output_path.read_text(encoding="utf-8"))

    assert report["subset_name"] == "golden"
    assert written_report["subset_name"] == "golden"
    assert written_report["run_summary"]["evaluated_sample_ids"] == [
        "curated_golden_001",
        "curated_golden_repeat_001",
    ]


def test_roadmap_2_10_entrypoint_uses_versioned_manifest_metadata(tmp_path, capsys):
    output_path = tmp_path / "roadmap_2_10" / "golden_v1_report.json"

    report = main(
        [
            "--roadmap-stage",
            "2.10",
            "--subset",
            "golden_v1",
            "--input-bundle",
            str(FIXTURE_BUNDLE_PATH),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    written_report = json.loads(output_path.read_text(encoding="utf-8"))

    assert written_report == report
    assert report["roadmap_stage"] == "2.10"
    assert report["subset_name"] == "golden_v1"
    assert report["manifest_metadata"] == {
        "manifest_version": "roadmap-2.10-golden-v1",
        "manifest_path": "evaluation/manifests/roadmap_2_10/golden_v1.json",
        "manifest_sample_count": 2,
    }
    assert report["run_summary"]["evaluated_sample_count"] == 2
    assert "subset=golden_v1" in captured.out
    assert "evaluated_samples=2" in captured.out


def test_roadmap_2_9_entrypoint_output_artifact_matches_stabilized_report_shape(tmp_path):
    output_path = tmp_path / "repeat_run_report.json"

    written_report = main(
        [
            "--subset",
            "repeat_run",
            "--input-bundle",
            str(FIXTURE_BUNDLE_PATH),
            "--output",
            str(output_path),
        ]
    )

    assert written_report == {
        "report_version": ROADMAP_2_9_EVALUATION_REPORT_VERSION,
        "roadmap_stage": "2.9",
        "subset_name": "repeat_run",
        "source_manifest": "samples.master.json",
        "run_summary": {
            "evaluated_sample_count": 2,
            "evaluated_sample_ids": [
                "curated_repeat_001",
                "curated_golden_repeat_001",
            ],
            "missing_sample_ids": [],
        },
        "warning_summary": {
            "warning_case_counts": {
                "llm_empty_output": 1,
                "no_shared_tags": 1,
            },
            "samples_with_warnings": [
                "curated_repeat_001",
                "curated_golden_repeat_001",
            ],
        },
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


def test_roadmap_2_9_entrypoint_uses_requested_output_path(tmp_path):
    output_path = tmp_path / "nested" / "artifact.json"

    main(
        [
            "--subset",
            "curated",
            "--input-bundle",
            str(FIXTURE_BUNDLE_PATH),
            "--output",
            str(output_path),
        ]
    )

    assert output_path.exists()
