import ast
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
ONNX_RUNTIME_DOC_PATH = SERVICE_ROOT / "docs/onnx-runtime.md"

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
    assert "essentia-tensorflow==2.1b6.dev1389" in production_requirements


def test_dockerfile_keeps_legacy_default_runtime_and_optional_onnx_target():
    dockerfile = _read_text(DOCKERFILE_PATH)

    assert "FROM runtime-base AS legacy-runtime" in dockerfile
    assert "FROM runtime-base AS onnx-runtime" in dockerfile
    assert "FROM runtime-base AS onnx-runtime-slim" in dockerfile
    assert dockerfile.index("FROM runtime-base AS legacy-runtime") < dockerfile.index(
        "FROM runtime-base AS onnx-runtime"
    )
    assert dockerfile.index("FROM runtime-base AS onnx-runtime") < dockerfile.index(
        "FROM runtime-base AS onnx-runtime-slim"
    )
    assert dockerfile.count("COPY requirements.txt /app/requirements.txt") == 3
    assert "COPY requirements-optional-onnx.txt /app/requirements-optional-onnx.txt" in dockerfile
    assert dockerfile.count("pip install --no-cache-dir --requirement /app/requirements.txt") == 2
    assert dockerfile.count("pip install --no-cache-dir --requirement /app/requirements-optional-onnx.txt") == 2
    assert "python -m pip uninstall -y tensorflow" in dockerfile
    assert "grep -vE '^[[:space:]]*tensorflow" in dockerfile
    assert "COPY app /app/app" in dockerfile
    assert "model.onnx" not in dockerfile
    assert "model.json" not in dockerfile
    assert "runtime downloads" not in dockerfile.lower()


def test_compose_switches_default_service_and_preserves_legacy_rollback_profile():
    compose = _read_text(COMPOSE_PATH)

    assert re.search(r"^\s*target:\s*onnx-runtime-slim\s*$", compose, re.MULTILINE)
    assert re.search(r"^\s*target:\s*legacy-runtime\s*$", compose, re.MULTILINE)
    assert re.search(r"^\s*target:\s*onnx-runtime\s*$", compose, re.MULTILINE) is None
    assert "profiles:" in compose
    assert "legacy" in compose
    assert "onnx_musicnn" in compose
    assert compose.count("GENRE_PROVIDER: onnx_musicnn") == 2
    assert "GENRE_PROVIDER: legacy_musicnn" in compose
    assert "ONNX_MUSICNN_MODEL_PATH: /opt/genre-classifier/onnx/msd-musicnn-1.onnx" in compose
    assert "ONNX_MUSICNN_METADATA_PATH: /opt/genre-classifier/onnx/msd-musicnn-1.json" in compose
    assert (
        compose.count(
            "/opt/music-tools-artifacts/genre-classifier/onnx:/opt/genre-classifier/onnx:ro"
        )
        == 2
    )
    assert "./artifacts/onnx-musicnn/model.onnx" not in compose
    assert "./artifacts/onnx-musicnn/model.json" not in compose
    default_service = compose.split("genre-classifier:\n", 1)[1].split(
        "genre-classifier-legacy:\n", 1
    )[0]
    assert "GENRE_PROVIDER: onnx_musicnn" in default_service
    assert "ONNX_MUSICNN_MODEL_PATH: /opt/genre-classifier/onnx/msd-musicnn-1.onnx" in default_service
    assert "ONNX_MUSICNN_METADATA_PATH: /opt/genre-classifier/onnx/msd-musicnn-1.json" in default_service
    legacy_service = compose.split("genre-classifier-legacy:\n", 1)[1].split(
        "genre-classifier-onnx:\n", 1
    )[0]
    assert "GENRE_PROVIDER: legacy_musicnn" in legacy_service
    assert "ONNX_MUSICNN_MODEL_PATH" not in legacy_service
    assert "ONNX_MUSICNN_METADATA_PATH" not in legacy_service
    assert "requirements-optional-onnx.txt" not in compose


def test_settings_switch_default_provider_to_onnx_and_keep_legacy_available():
    settings_text = _read_text(SETTINGS_PATH)
    factory_text = _read_text(FACTORY_PATH)

    assert settings.DEFAULT_GENRE_PROVIDER == settings.GENRE_PROVIDER_ONNX == "onnx_musicnn"
    assert settings.GENRE_PROVIDER_LEGACY == "legacy_musicnn"
    assert settings.DEFAULT_ONNX_MUSICNN_MODEL_PATH is None
    assert settings.DEFAULT_ONNX_MUSICNN_METADATA_PATH is None
    assert settings.GENRE_PROVIDER_ONNX == "onnx_musicnn"
    assert settings_text.count('DEFAULT_GENRE_PROVIDER = "onnx_musicnn"') == 1
    assert settings_text.count("DEFAULT_ONNX_MUSICNN_MODEL_PATH = None") == 1
    assert settings_text.count("DEFAULT_ONNX_MUSICNN_METADATA_PATH = None") == 1
    assert "if provider_name == genre_provider_onnx:" in factory_text
    assert "return OnnxMusiCNNProvider(settings_module=settings)" in factory_text


def test_onnx_runtime_docs_cover_current_operator_contract():
    doc = _read_text(ONNX_RUNTIME_DOC_PATH)

    assert ONNX_RUNTIME_DOC_PATH.is_file()
    assert "onnx_musicnn" in doc
    assert "onnx-runtime-slim" in doc
    assert "/opt/music-tools-artifacts/genre-classifier/onnx" in doc
    assert "msd-musicnn-1.onnx" in doc
    assert "msd-musicnn-1.json" in doc
    assert "genre-classifier-legacy" in doc


def test_classify_contract_and_response_shape_remain_unchanged():
    route_keys = _extract_classify_return_dict_keys(ROUTES_PATH)

    assert {"ok", "error"} in route_keys
    assert {"ok", "message", "genres", "genres_pretty"} in route_keys
    assert len({"ok", "message", "genres", "genres_pretty"}) == 4
    assert "Аудио проанализировано" in _read_text(ROUTES_PATH)
