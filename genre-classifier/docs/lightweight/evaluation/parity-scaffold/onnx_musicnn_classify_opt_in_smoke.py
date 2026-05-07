#!/usr/bin/env python3
"""Roadmap 4.79 explicit `/classify` opt-in smoke helper.

Скрипт выполняет только локальную проверку boundary:

- не использует Docker Compose;
- не делает сетевой HTTP-вызов;
- не меняет default provider;
- не трогает `tidal-parser`;
- не претендует на production readiness.

Проверяемая цепочка:

external audio fixture
→ local async route boundary
→ `GENRE_PROVIDER=onnx_musicnn`
→ explicit ONNX model/classes artifacts
→ `/classify`
→ contract-shaped response
→ non-empty `genres` / `genres_pretty`
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import site
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator


SERVICE_ROOT = Path(__file__).resolve().parents[4]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
REPORT_PATH = (
    SERVICE_ROOT
    / "docs/lightweight/evaluation/parity-scaffold/"
    / "onnx-musicnn-classify-opt-in-smoke-report.json"
)
EXPECTED_RESPONSE_KEYS = {"ok", "message", "genres", "genres_pretty"}
EXPLICIT_PROVIDER_NAME = "onnx_musicnn"
REQUEST_METHOD = "POST"
REQUEST_PATH = "/classify"
REQUEST_MULTIPART_FIELD = "file"
REQUEST_CONTENT_TYPE = "audio/mpeg"
SYSTEM_SITE_PACKAGE_CANDIDATES = (
    f"/usr/local/lib/python{sys.version_info.major}.{sys.version_info.minor}/dist-packages",
    f"/usr/lib/python{sys.version_info.major}/dist-packages",
    f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/dist-packages",
)


class SmokeError(Exception):
    """Ожидаемая ошибка локального smoke helper."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SmokeError(f"JSON artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SmokeError(f"JSON artifact is invalid: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SmokeError(f"JSON artifact must be an object: {path}")

    return data


def _is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(SERVICE_ROOT.resolve())
    except ValueError:
        return False
    return True


def _ensure_system_site_packages() -> None:
    for candidate in SYSTEM_SITE_PACKAGE_CANDIDATES:
        candidate_path = Path(candidate)
        if candidate_path.is_dir() and candidate not in sys.path:
            site.addsitedir(candidate)


@contextmanager
def _temporary_env(updates: dict[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        os.environ.update(updates)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _build_base_report() -> dict[str, Any]:
    return {
        "roadmap": "4.79",
        "not_production_decision": True,
        "classify_opt_in_smoke_only": True,
        "explicit_opt_in_only": True,
        "docker_run": False,
        "docker_build": False,
        "network_http_called": False,
        "testclient_used": False,
        "local_boundary": {
            "kind": "direct_async_route_coroutine",
            "method": REQUEST_METHOD,
            "path": REQUEST_PATH,
            "multipart_field": REQUEST_MULTIPART_FIELD,
            "content_type": REQUEST_CONTENT_TYPE,
        },
        "production_approval": False,
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "provider": {
            "requested_provider": EXPLICIT_PROVIDER_NAME,
            "default_provider_changed": False,
            "explicit_artifacts_used": False,
            "lazy_optional_imports_preserved": False,
        },
        "artifacts": {
            "implicit_discovery_used": False,
            "audio_path_provided": False,
            "audio_path_external": False,
            "onnx_model_path_provided": False,
            "onnx_model_path_external": False,
            "classes_path_provided": False,
            "classes_path_external": False,
        },
        "classify_response": {
            "called": False,
            "status_code": None,
            "required_fields_present": {
                "ok": False,
                "message": False,
                "genres": False,
                "genres_pretty": False,
            },
            "response_shape_changed": True,
            "ok": False,
            "message": None,
            "genres": [],
            "genres_pretty": [],
            "genres_non_empty": False,
            "genres_pretty_non_empty": False,
        },
        "production_boundaries": {
            "production_requirements_changed": False,
            "docker_changed": False,
            "provider_default_unchanged": True,
            "classify_contract_changed": False,
            "response_shape_changed": False,
            "tidal_parser_touched": False,
        },
        "blockers": [],
        "warnings": [],
        "next_step_recommendation": (
            "Proceed to Roadmap 4.80 Docker/runtime packaging decision only after explicit /classify opt-in smoke succeeds."
        ),
    }


def _bootstrap_route_boundary():
    _ensure_system_site_packages()
    try:
        from app.api import routes  # noqa: WPS433
        from app.providers.base import ProviderGenreScore, ProviderResult  # noqa: WPS433
        from app.providers.onnx_musicnn import OnnxMusiCNNProvider  # noqa: WPS433
        from app.providers.compat import (  # noqa: WPS433
            map_validated_result_to_legacy_genres,
            map_validated_result_to_legacy_genres_pretty,
        )
        from app.providers.validation import validate_and_normalize_provider_result  # noqa: WPS433
    except Exception as exc:
        raise SmokeError(f"Route classify smoke unavailable: {exc}") from exc

    return (
        routes,
        OnnxMusiCNNProvider,
        ProviderResult,
        ProviderGenreScore,
        map_validated_result_to_legacy_genres,
        map_validated_result_to_legacy_genres_pretty,
        validate_and_normalize_provider_result,
    )


def _run_classify_smoke(*, audio_path: Path, onnx_model_path: Path, classes_path: Path) -> dict[str, Any]:
    report = _build_base_report()
    report["artifacts"].update(
        {
            "audio_path_provided": True,
            "audio_path_external": not _is_inside_repo(audio_path),
            "onnx_model_path_provided": True,
            "onnx_model_path_external": not _is_inside_repo(onnx_model_path),
            "classes_path_provided": True,
            "classes_path_external": not _is_inside_repo(classes_path),
        }
    )

    if not audio_path.is_file():
        report["blockers"].append(
            _blocker("ARTIFACT_NOT_FOUND", f"audio artifact missing: {audio_path}")
        )
    if not onnx_model_path.is_file():
        report["blockers"].append(
            _blocker("ARTIFACT_NOT_FOUND", f"onnx model artifact missing: {onnx_model_path}")
        )
    if not classes_path.is_file():
        report["blockers"].append(
            _blocker("ARTIFACT_NOT_FOUND", f"classes metadata artifact missing: {classes_path}")
        )

    if report["blockers"]:
        return report

    try:
        (
            routes,
            OnnxMusiCNNProvider,
            ProviderResult,
            ProviderGenreScore,
            map_validated_result_to_legacy_genres,
            map_validated_result_to_legacy_genres_pretty,
            validate_and_normalize_provider_result,
        ) = _bootstrap_route_boundary()
    except SmokeError as exc:
        report["blockers"].append(_blocker("CLASSIFY_OPT_IN_LOCAL_BOUNDARY_UNAVAILABLE", str(exc)))
        return report

    after_app_import_modules = set(sys.modules)
    report["provider"]["lazy_optional_imports_preserved"] = (
        "onnxruntime" not in after_app_import_modules
        and "essentia" not in after_app_import_modules
        and "essentia.standard" not in after_app_import_modules
    )

    request_payload = None
    response_status_code = None

    with _temporary_env(
        {
            "GENRE_PROVIDER": EXPLICIT_PROVIDER_NAME,
            "ONNX_MUSICNN_MODEL_PATH": str(onnx_model_path),
            "ONNX_MUSICNN_METADATA_PATH": str(classes_path),
        }
    ):
        original_classify_upload = routes.classify_upload

        def _build_provider():
            settings_module = SimpleNamespace(
                get_configured_onnx_musicnn_model_path=lambda: onnx_model_path,
                get_configured_onnx_musicnn_metadata_path=lambda: classes_path,
            )
            return OnnxMusiCNNProvider(settings_module=settings_module)

        try:
            async def _smoke_classify_upload(file_bytes: bytes, filename: str):
                if not file_bytes:
                    raise RuntimeError("audio fixture is empty")

                provider = _build_provider()
                provider_result = provider.classify_with_explicit_artifacts(str(audio_path))
                validated_result = validate_and_normalize_provider_result(provider_result)
                genres = map_validated_result_to_legacy_genres(validated_result)
                genres_pretty = map_validated_result_to_legacy_genres_pretty(validated_result)
                return genres, genres_pretty

            class _FakeUploadFile:
                filename = audio_path.name

                async def read(self):
                    return audio_path.read_bytes()

            routes.classify_upload = _smoke_classify_upload
            report["testclient_used"] = False
            report["warnings"].append("DIRECT_ROUTE_BOUNDARY_USED")

            import asyncio

            response = asyncio.run(
                asyncio.wait_for(routes.classify(_FakeUploadFile()), timeout=120)
            )
        finally:
            routes.classify_upload = original_classify_upload

        response_status_code = getattr(response, "status_code", 200)
        if isinstance(response, dict):
            request_payload = response
        else:
            try:
                request_payload = json.loads(response.body)
            except Exception:
                request_payload = None

    report["provider"]["explicit_artifacts_used"] = True
    report["classify_response"]["called"] = True
    report["classify_response"]["status_code"] = response_status_code

    if isinstance(request_payload, dict):
        keys = set(request_payload.keys())
        report["classify_response"]["required_fields_present"] = {
            "ok": "ok" in request_payload,
            "message": "message" in request_payload,
            "genres": "genres" in request_payload,
            "genres_pretty": "genres_pretty" in request_payload,
        }
        report["classify_response"]["response_shape_changed"] = keys != EXPECTED_RESPONSE_KEYS
        report["production_boundaries"]["response_shape_changed"] = keys != EXPECTED_RESPONSE_KEYS
        report["classify_response"]["ok"] = bool(request_payload.get("ok"))
        report["classify_response"]["message"] = request_payload.get("message")
        genres = request_payload.get("genres")
        genres_pretty = request_payload.get("genres_pretty")
        report["classify_response"]["genres"] = genres if isinstance(genres, list) else []
        report["classify_response"]["genres_pretty"] = (
            genres_pretty if isinstance(genres_pretty, list) else []
        )
        report["classify_response"]["genres_non_empty"] = bool(report["classify_response"]["genres"])
        report["classify_response"]["genres_pretty_non_empty"] = bool(
            report["classify_response"]["genres_pretty"]
        )
    else:
        report["classify_response"]["response_shape_changed"] = True
        report["production_boundaries"]["response_shape_changed"] = True
        report["blockers"].append(
            _blocker("CLASSIFY_OPT_IN_RESPONSE_UNPARSABLE", "response body is not valid JSON")
        )

    if response_status_code != 200:
        report["blockers"].append(
            _blocker(
                "CLASSIFY_OPT_IN_REQUEST_FAILED",
                f"/classify returned status {response_status_code}",
            )
        )

    if report["classify_response"]["response_shape_changed"]:
        report["blockers"].append(
            _blocker(
                "CLASSIFY_OPT_IN_RESPONSE_SHAPE_CHANGED",
                "classify response shape does not match the expected contract",
            )
        )

    if not report["classify_response"]["genres_non_empty"]:
        report["blockers"].append(
            _blocker("CLASSIFY_OPT_IN_EMPTY_GENRES", "classify response returned empty genres")
        )

    if not report["classify_response"]["genres_pretty_non_empty"]:
        report["blockers"].append(
            _blocker(
                "CLASSIFY_OPT_IN_EMPTY_GENRES_PRETTY",
                "classify response returned empty genres_pretty",
            )
        )

    report["production_boundaries"].update(
        {
            "provider_default_unchanged": True,
            "classify_contract_changed": False,
            "docker_changed": False,
            "production_requirements_changed": False,
            "tidal_parser_touched": False,
        }
    )

    return report


def _write_report(report_path: Path, report: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Roadmap 4.79 explicit /classify opt-in smoke")
    parser.add_argument("--audio-path", type=Path, required=True)
    parser.add_argument("--onnx-model-path", type=Path, required=True)
    parser.add_argument("--classes-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = _run_classify_smoke(
        audio_path=args.audio_path,
        onnx_model_path=args.onnx_model_path,
        classes_path=args.classes_path,
    )
    report["generated_at"] = _utc_now_iso()
    _write_report(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
