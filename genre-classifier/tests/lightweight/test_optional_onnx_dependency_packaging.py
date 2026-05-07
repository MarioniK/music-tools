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
    / "onnx-musicnn-optional-dependency-packaging-validation-report.json"
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


def test_dockerfile_and_compose_do_not_enable_optional_install_or_onnx_default():
    dockerfile = _read_text(DOCKERFILE_PATH)
    compose = _read_text(COMPOSE_PATH)

    assert "requirements-optional-onnx.txt" not in dockerfile
    assert "requirements-optional-onnx.txt" not in compose
    assert "onnx_musicnn" not in compose
    assert "GENRE_PROVIDER=onnx_musicnn" not in compose


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

    assert report["roadmap"] == "4.74"
    assert report["validation_gate"] is True
    assert report["not_production_decision"] is True
    assert report["optional_requirements_present"] is True
    assert report["optional_requirements_file"] == "genre-classifier/requirements-optional-onnx.txt"
    assert report["expected_pinned_dependencies"] == EXPECTED_OPTIONAL_REQUIREMENTS
    assert report["pinned_dependencies_valid"] is True
    assert report["production_requirements_reference_optional_file"] is False
    assert report["production_requirements_include_onnxruntime"] is False
    assert report["production_requirements_include_essentia_tensorflow"] is False
    assert report["docker_installs_optional_requirements"] is False
    assert report["compose_sets_onnx_provider_by_default"] is False
    assert report["provider_default_unchanged"] is True
    assert report["default_provider"] == "legacy_musicnn"
    assert report["onnx_musicnn_disabled_by_default"] is True
    assert report["classify_contract_unchanged"] is True
    assert report["response_shape_unchanged"] is True
    assert report["runtime_smoke_approved"] is False
    assert report["production_approval"] is False
    assert report["production_dependency_changes"] is False
    assert report["docker_changes"] is False
    assert report["tidal_parser_touched"] is False
    assert report["blockers"] == []
    assert (
        report["next_step_recommendation"]
        == "Roadmap 4.75 may perform an isolated optional install probe only after explicit approval, without Docker/runtime migration."
    )
