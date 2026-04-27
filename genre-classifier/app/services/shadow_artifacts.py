import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from app.services.runtime_shadow import ShadowRunOutcome


SHADOW_EVIDENCE_SCHEMA_VERSION = "runtime_shadow_v1"


@dataclass(frozen=True)
class ShadowArtifactWriteResult:
    success: bool
    path: Optional[str]
    error_type: Optional[str] = None
    error_message: Optional[str] = None


def build_shadow_evidence_payload(
    *,
    request_id: Optional[str],
    production_provider: str,
    shadow_provider: str,
    legacy_tags: Sequence[str],
    outcome: ShadowRunOutcome,
    input_fingerprint: Optional[str] = None,
    timestamp_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a JSON-safe runtime shadow evidence payload without raw audio or prompts."""
    return {
        "schema_version": SHADOW_EVIDENCE_SCHEMA_VERSION,
        "timestamp_utc": timestamp_utc or _utc_timestamp(),
        "request_id": request_id,
        "input": {
            "input_fingerprint": input_fingerprint,
        },
        "providers": {
            "production": production_provider,
            "shadow": shadow_provider,
        },
        "legacy": {
            "tags": list(legacy_tags),
        },
        "shadow": {
            "status": outcome.status,
            "tags": list(outcome.shadow_tags),
            "duration_ms": outcome.duration_ms,
            "error_type": outcome.error_type,
            "error_message": outcome.error_message,
        },
        "comparison": _comparison_to_payload(outcome.comparison),
    }


def append_shadow_evidence_jsonl(
    payload: Dict[str, Any],
    *,
    artifact_path: Optional[Path] = None,
    artifacts_dir: Optional[Path] = None,
    filename: str = "runtime_shadow.jsonl",
) -> ShadowArtifactWriteResult:
    path = Path(artifact_path) if artifact_path is not None else Path(artifacts_dir or ".") / filename

    try:
        line = json.dumps(payload, ensure_ascii=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as artifact_file:
            artifact_file.write(line)
            artifact_file.write("\n")
    except (OSError, TypeError, ValueError) as exc:
        return ShadowArtifactWriteResult(
            success=False,
            path=str(path),
            error_type=type(exc).__name__,
            error_message=str(exc)[:200],
        )

    return ShadowArtifactWriteResult(success=True, path=str(path))


def _comparison_to_payload(comparison):
    if comparison is None:
        return None

    if hasattr(comparison, "to_dict"):
        return comparison.to_dict()

    if isinstance(comparison, dict):
        return dict(comparison)

    return comparison


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
