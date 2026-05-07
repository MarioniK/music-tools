import ast
import json
import re
from pathlib import Path

from app.core import settings


SERVICE_ROOT = Path(__file__).resolve().parents[2]
OPTIONAL_REQUIREMENTS_PATH = SERVICE_ROOT / "requirements-optional-onnx.txt"
PRODUCTION_REQUIREMENTS_PATH = SERVICE_ROOT / "requirements.txt"
DOCKERFILE_PATH = SERVICE_ROOT / "Dockerfile"
COMPOSE_PATH = SERVICE_ROOT / "docker-compose.yml"
ROUTES_PATH = SERVICE_ROOT / "app/api/routes.py"
SETTINGS_PATH = SERVICE_ROOT / "app/core/settings.py"
FACTORY_PATH = SERVICE_ROOT / "app/providers/factory.py"
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-optional-docker-target-profile-report.json"
)
BUILD_VALIDATION_REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-optional-docker-build-validation-report.json"
)

EXPECTED_OPTIONAL_REQUIREMENTS = [
    "onnxruntime==1.25.1",
    "essentia-tensorflow==2.1b6.dev1389",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_requirement_entries(path: Path) -> list[str]:
    entries: list[str] = []
    for raw_line in _read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line)
    return entries


def _requirement_package_name(requirement_line: str) -> str:
    return re.split(r"[<>=!~;\[]", requirement_line, maxsplit=1)[0].strip().lower()


def _assert_no_forbidden_requirement_forms(requirement_line: str, context: str) -> None:
    forbidden_fragments = (
        "-e ",
        "git+",
        "http://",
        "https://",
        "file:",
        "pip install",
        "curl ",
        "wget ",
        "python ",
        ".sh",
        "../",
        "./",
    )
    for fragment in forbidden_fragments:
        assert fragment not in requirement_line.lower(), f"{context} must not contain {fragment!r}"


def _extract_classify_return_dict_keys(path: Path) -> list[set[str]]:
    tree = ast.parse(_read_text(path))
    dict_key_sets: list[set[str]] = []

    class _Visitor(ast.NodeVisitor):
        def _visit_function(self, node):
            if node.name == "classify":
                for child in ast.walk(node):
                    if isinstance(child, ast.Dict):
                        keys = {
                            key.value
                            for key in child.keys
                            if isinstance(key, ast.Constant) and isinstance(key.value, str)
                        }
                        if keys:
                            dict_key_sets.append(keys)
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            self._visit_function(node)

        def visit_AsyncFunctionDef(self, node):
            self._visit_function(node)

    _Visitor().visit(tree)
    return dict_key_sets


def test_optional_requirements_file_has_expected_pinned_dependencies():
    assert OPTIONAL_REQUIREMENTS_PATH.is_file()

    entries = _read_requirement_entries(OPTIONAL_REQUIREMENTS_PATH)
    assert entries == EXPECTED_OPTIONAL_REQUIREMENTS

    for entry in entries:
        context = f"{OPTIONAL_REQUIREMENTS_PATH.name}:{entry}"
        _assert_no_forbidden_requirement_forms(entry, context)
        package_name = _requirement_package_name(entry)
        assert package_name not in {"onnxruntime-gpu", "tensorflow"}
        assert "==" in entry


def test_optional_requirements_file_does_not_contain_forbidden_dependency_forms():
    entries = _read_requirement_entries(OPTIONAL_REQUIREMENTS_PATH)

    forbidden_tokens = (
        "onnxruntime-gpu",
        "-e ",
        "git+",
        "http://",
        "https://",
        "file:",
        "pip install",
        "curl ",
        "wget ",
        ".sh",
    )
    for entry in entries:
        lower_entry = entry.lower()
        for token in forbidden_tokens:
            assert token not in lower_entry
        assert _requirement_package_name(entry) not in {"onnxruntime-gpu", "tensorflow"}


def test_production_requirements_remain_separate_from_optional_packaging():
    production_requirements = _read_text(PRODUCTION_REQUIREMENTS_PATH)

    assert "requirements-optional-onnx.txt" not in production_requirements
    assert "onnxruntime" not in production_requirements
    assert "essentia-tensorflow" not in production_requirements
    assert "tensorflow==2.21.0" in production_requirements


def test_dockerfile_keeps_legacy_default_runtime_and_optional_onnx_target():
    dockerfile = _read_text(DOCKERFILE_PATH)

    assert "FROM runtime-base AS legacy-runtime" in dockerfile
    assert "FROM runtime-base AS onnx-runtime" in dockerfile
    assert "COPY requirements.txt /app/requirements.txt" in dockerfile
    assert "pip install --no-cache-dir --requirement /app/requirements.txt" in dockerfile
    assert "COPY requirements-optional-onnx.txt /app/requirements-optional-onnx.txt" in dockerfile
    assert "pip install --no-cache-dir --requirement /app/requirements-optional-onnx.txt" in dockerfile
    assert dockerfile.index("COPY requirements.txt /app/requirements.txt") < dockerfile.index(
        "COPY requirements-optional-onnx.txt /app/requirements-optional-onnx.txt"
    )
    assert "COPY app /app/app" in dockerfile
    assert "model.onnx" not in dockerfile
    assert "model.json" not in dockerfile
    assert "runtime downloads" not in dockerfile.lower()


def test_compose_adds_optional_onnx_profile_without_switching_default_service():
    compose = _read_text(COMPOSE_PATH)

    assert "target: legacy-runtime" in compose
    assert "target: onnx-runtime" in compose
    assert "profiles:" in compose
    assert "onnx_musicnn" in compose
    assert "GENRE_PROVIDER: onnx_musicnn" in compose
    assert "ONNX_MUSICNN_MODEL_PATH: /opt/genre-classifier/onnx/model.onnx" in compose
    assert "ONNX_MUSICNN_METADATA_PATH: /opt/genre-classifier/onnx/model.json" in compose
    assert "./artifacts/onnx-musicnn/model.onnx:/opt/genre-classifier/onnx/model.onnx:ro" in compose
    assert "./artifacts/onnx-musicnn/model.json:/opt/genre-classifier/onnx/model.json:ro" in compose
    assert "requirements-optional-onnx.txt" not in compose


def test_settings_keep_legacy_default_provider_and_disabled_by_default_onnx():
    settings_text = _read_text(SETTINGS_PATH)
    factory_text = _read_text(FACTORY_PATH)

    assert settings.DEFAULT_GENRE_PROVIDER == settings.GENRE_PROVIDER_LEGACY == "legacy_musicnn"
    assert settings.DEFAULT_ONNX_MUSICNN_MODEL_PATH is None
    assert settings.DEFAULT_ONNX_MUSICNN_METADATA_PATH is None
    assert settings.GENRE_PROVIDER_ONNX == "onnx_musicnn"
    assert settings_text.count('DEFAULT_GENRE_PROVIDER = "legacy_musicnn"') == 1
    assert settings_text.count("DEFAULT_ONNX_MUSICNN_MODEL_PATH = None") == 1
    assert settings_text.count("DEFAULT_ONNX_MUSICNN_METADATA_PATH = None") == 1
    assert "if provider_name == genre_provider_onnx:" in factory_text
    assert "return OnnxMusiCNNProvider(settings_module=settings)" in factory_text


def test_classify_contract_and_response_shape_remain_unchanged():
    route_keys = _extract_classify_return_dict_keys(ROUTES_PATH)

    assert {"ok", "error"} in route_keys
    assert {"ok", "message", "genres", "genres_pretty"} in route_keys
    assert len({"ok", "message", "genres", "genres_pretty"}) == 4
    assert "Аудио проанализировано" in _read_text(ROUTES_PATH)


def test_optional_packaging_report_records_current_static_state():
    report = json.loads(_read_text(REPORT_PATH))

    assert report["roadmap"] == "4.81"
    assert report["optional_docker_packaging_implementation"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["docker_build_run"] is False
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    implementation = report["implementation"]
    assert implementation["dockerfile_changed"] is True
    assert implementation["compose_changed"] is True
    assert implementation["optional_target_added"] is True
    assert implementation["optional_profile_added"] is True
    assert implementation["optional_build_arg_added"] is False
    assert implementation["default_install_path_unchanged"] is True
    assert implementation["optional_requirements_installed_only_in_optional_path"] is True
    assert implementation["runtime_downloads_by_default"] is False
    assert implementation["artifacts_baked_into_image"] is False
    assert implementation["mounted_artifacts_required"] is True
    default_runtime = report["default_runtime"]
    assert default_runtime["provider"] == "legacy_musicnn"
    assert default_runtime["legacy_only"] is True
    assert default_runtime["installs_optional_onnx_deps"] is False
    assert default_runtime["uses_requirements_optional_onnx"] is False
    optional_runtime = report["optional_onnx_runtime"]
    assert optional_runtime["provider"] == "onnx_musicnn"
    assert optional_runtime["explicit_opt_in_only"] is True
    assert optional_runtime["uses_requirements_optional_onnx"] is True
    assert optional_runtime["requires_explicit_model_path"] is True
    assert optional_runtime["requires_explicit_classes_path"] is True
    assert optional_runtime["artifacts_delivery"] == "mounted_paths"
    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False
    validation = report["validation"]
    assert validation["roadmap_4_80_report_json_valid"] is True
    assert validation["requirements_optional_onnx_pinned"] is True
    assert validation["production_requirements_clean"] is True
    assert validation["static_validation_passed"] is True
    assert report["blockers"] == []
    assert report["warnings"] == []
    assert (
        report["next_step_recommendation"]
        == "Roadmap 4.82 - optional Docker build/static runtime validation without default switch."
    )


def test_optional_docker_build_validation_report_records_runtime_checks():
    report = json.loads(_read_text(BUILD_VALIDATION_REPORT_PATH))

    assert report["roadmap"] == "4.82"
    assert report["optional_docker_build_validation"] is True
    assert report["not_production_decision"] is True
    assert report["production_approval"] is False
    assert report["docker_build_run"] is True
    assert report["docker_compose_run"] is False
    assert report["classify_called"] is False
    assert report["network_http_called"] is False
    assert report["production_inference_run"] is False

    docker = report["docker"]
    assert docker["context"] == "genre-classifier"
    assert docker["target"] == "onnx-runtime"
    assert docker["image_tag"] == "music-tools-genre-classifier-onnx:roadmap-4.82"
    assert docker["build_success"] is True
    assert docker["build_duration_seconds"] == 124
    assert (
        docker["image_id"]
        == "sha256:c1c8101f93012ce23a545b7f5c95ef28732825343e253443e9c94995271ac1d7"
    )
    assert docker["image_size"] == 3479268978

    runtime_checks = report["runtime_static_checks"]
    assert runtime_checks["pip_show_onnxruntime_ok"] is True
    assert runtime_checks["pip_show_essentia_tensorflow_ok"] is True
    assert runtime_checks["onnxruntime_import_ok"] is True
    assert runtime_checks["onnxruntime_version"] == "1.25.1"
    assert runtime_checks["onnxruntime_available_providers"] == [
        "AzureExecutionProvider",
        "CPUExecutionProvider",
    ]
    assert runtime_checks["essentia_import_ok"] is True
    assert runtime_checks["essentia_standard_import_ok"] is True
    assert runtime_checks["tensorflow_input_musicnn_available"] is True

    default_runtime = report["default_runtime"]
    assert default_runtime["provider"] == "legacy_musicnn"
    assert default_runtime["legacy_only"] is True
    assert default_runtime["build_run"] is False
    assert default_runtime["compose_run"] is False

    optional_runtime = report["optional_onnx_runtime"]
    assert optional_runtime["provider"] == "onnx_musicnn"
    assert optional_runtime["explicit_opt_in_only"] is True
    assert optional_runtime["uses_requirements_optional_onnx"] is True
    assert optional_runtime["artifacts_delivery"] == "mounted_paths"
    assert optional_runtime["artifacts_baked_into_image"] is False
    assert optional_runtime["runtime_downloads_by_default"] is False

    production_boundaries = report["production_boundaries"]
    assert production_boundaries["production_requirements_changed"] is False
    assert production_boundaries["default_provider_changed"] is False
    assert production_boundaries["classify_contract_changed"] is False
    assert production_boundaries["response_shape_changed"] is False
    assert production_boundaries["tidal_parser_touched"] is False

    assert report["blockers"] == []
    assert report["warnings"] == [
        "TensorFlow/CUDA warnings appeared during import checks but did not block validation.",
        "No /classify or network HTTP smoke was run in this roadmap step.",
    ]
    assert (
        report["next_step_recommendation"]
        == "Roadmap 4.83 - optional ONNX Compose profile config/static validation or optional container smoke without /classify, depending on 4.82 outcome."
    )
