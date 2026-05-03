#!/usr/bin/env python3
"""Offline-only ONNX candidate spike dry-run scaffold.

This script intentionally uses only the Python standard library and does not
import production app, provider, cache, runtime, or inference modules.
"""

import argparse
import json
from pathlib import Path
from typing import Any


DRY_RUN_MESSAGE = (
    "dry-run only; no ONNX Runtime loaded; no model loaded; "
    "no audio processed; no inference executed"
)


def build_dry_run_output() -> dict[str, Any]:
    return {
        "ok": True,
        "message": DRY_RUN_MESSAGE,
        "genres": [
            {
                "tag": "electronic",
                "prob": 0.0,
            }
        ],
        "genres_pretty": ["Electronic"],
    }


def write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the offline-only ONNX candidate spike dry-run scaffold."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="Emit a dry-run summary without loading ONNX Runtime, model, audio, or inference code.",
    )
    parser.add_argument(
        "--write-output",
        type=Path,
        help="Optional explicit path for a /classify-compatible JSON dry-run artifact.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    payload = build_dry_run_output()
    print("ONNX candidate spike scaffold dry-run")
    print(f"message: {payload['message']}")
    print("result: no runtime dependency, no model, no audio, no inference")

    if args.write_output is not None:
        write_output(args.write_output, payload)
        print(f"wrote output: {args.write_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
