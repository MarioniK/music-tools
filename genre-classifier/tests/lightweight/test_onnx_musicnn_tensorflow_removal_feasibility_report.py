import json
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-tensorflow-removal-feasibility-report.json"
)


def test_onnx_musicnn_tensorflow_removal_feasibility_report_is_structurally_valid():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    assert report["roadmap"] == "4.84"
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["reused_existing_image"] is True
    assert report["rebuild_run"] is False
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    assert report["original_image_unchanged"] is True
    assert report["tensorflow_removed_only_in_disposable_container"] is True
    assert report["package_state"]["tensorflow_present_before_uninstall"] is True
    assert report["package_state"]["tensorflow_present_after_uninstall"] is False
    assert report["package_state"]["essentia_tensorflow_present_after_uninstall"] is True
    assert report["imports_after_uninstall"]["tensorflow_import_ok"] is False
    assert report["imports_after_uninstall"]["essentia_import_ok"] is True
    assert report["imports_after_uninstall"]["essentia_standard_import_ok"] is True
    assert report["imports_after_uninstall"]["onnxruntime_import_ok"] is True
    assert report["full_pipeline_after_uninstall"]["success"] is True
    assert report["full_pipeline_after_uninstall"]["patch_shape"] == [187, 96]
    assert report["full_pipeline_after_uninstall"]["patch_shape_match"] is True
    assert report["full_pipeline_after_uninstall"]["activations_shape"] == [50]
    assert report["full_pipeline_after_uninstall"]["embeddings_shape"] == [200]
    assert report["full_pipeline_after_uninstall"]["classes_activations_count_match"] is True
    assert report["full_pipeline_after_uninstall"]["genres_non_empty"] is True
    assert report["full_pipeline_after_uninstall"]["genres_pretty_non_empty"] is True
    assert report["decision_signal"]["tensorflow_python_package_removable_candidate"] is True
    assert report["production_boundaries"]["tidal_parser_touched"] is False
