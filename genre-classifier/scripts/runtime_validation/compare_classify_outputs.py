#!/usr/bin/env python3
"""Compare saved /classify outputs from two isolated runtimes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def read_meta(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    result: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def read_json(path: Path) -> Tuple[Optional[Any], Optional[str]]:
    if not path.exists():
        return None, "missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, f"json parse error: {exc}"


def genre_tags(payload: Any) -> List[str]:
    if not isinstance(payload, dict):
        return []
    genres = payload.get("genres")
    if not isinstance(genres, list):
        return []
    tags: List[str] = []
    for item in genres:
        if isinstance(item, dict):
            tag = item.get("tag")
            if isinstance(tag, str):
                tags.append(tag)
    return tags


def genre_scores(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    genres = payload.get("genres")
    if not isinstance(genres, list):
        return {}
    scores: Dict[str, Any] = {}
    for item in genres:
        if isinstance(item, dict) and isinstance(item.get("tag"), str):
            scores[item["tag"]] = item.get("prob")
    return scores


def genres_pretty(payload: Any) -> List[str]:
    if not isinstance(payload, dict):
        return []
    value = payload.get("genres_pretty")
    return value if isinstance(value, list) else []


def top_level_keys(payload: Any) -> List[str]:
    if isinstance(payload, dict):
        return sorted(str(key) for key in payload.keys())
    return []


def incompatible_shape(payload: Any) -> List[str]:
    issues: List[str] = []
    if not isinstance(payload, dict):
        return ["response is not a JSON object"]
    for key in ("ok", "message", "genres", "genres_pretty"):
        if key not in payload:
            issues.append(f"missing top-level key: {key}")
    if "genres" in payload and not isinstance(payload["genres"], list):
        issues.append("genres is not a list")
    if "genres_pretty" in payload and not isinstance(payload["genres_pretty"], list):
        issues.append("genres_pretty is not a list")
    for index, item in enumerate(payload.get("genres", []) if isinstance(payload.get("genres"), list) else []):
        if not isinstance(item, dict):
            issues.append(f"genres[{index}] is not an object")
            continue
        if "tag" not in item:
            issues.append(f"genres[{index}] missing tag")
        if "prob" not in item:
            issues.append(f"genres[{index}] missing prob")
    return issues


def overlap(left: Iterable[str], right: Iterable[str]) -> List[str]:
    right_set = set(right)
    return [item for item in left if item in right_set]


def compare_pair(name: str, baseline_dir: Path, candidate_dir: Path) -> Dict[str, Any]:
    baseline_body = baseline_dir / f"{name}.body.json"
    candidate_body = candidate_dir / f"{name}.body.json"
    baseline_meta = read_meta(baseline_dir / f"{name}.meta.txt")
    candidate_meta = read_meta(candidate_dir / f"{name}.meta.txt")
    baseline_payload, baseline_error = read_json(baseline_body)
    candidate_payload, candidate_error = read_json(candidate_body)
    baseline_tags = genre_tags(baseline_payload)
    candidate_tags = genre_tags(candidate_payload)
    shared = overlap(baseline_tags, candidate_tags)

    return {
        "name": name,
        "http_status": {
            "baseline": baseline_meta.get("HTTP_STATUS"),
            "candidate": candidate_meta.get("HTTP_STATUS"),
            "match": baseline_meta.get("HTTP_STATUS") == candidate_meta.get("HTTP_STATUS"),
        },
        "time_total": {
            "baseline": baseline_meta.get("TIME_TOTAL"),
            "candidate": candidate_meta.get("TIME_TOTAL"),
        },
        "json_parseability": {
            "baseline_ok": baseline_error is None,
            "candidate_ok": candidate_error is None,
            "baseline_error": baseline_error,
            "candidate_error": candidate_error,
        },
        "top_level_keys": {
            "baseline": top_level_keys(baseline_payload),
            "candidate": top_level_keys(candidate_payload),
            "match": top_level_keys(baseline_payload) == top_level_keys(candidate_payload),
        },
        "shape_issues": {
            "baseline": incompatible_shape(baseline_payload),
            "candidate": incompatible_shape(candidate_payload),
        },
        "genres_length": {
            "baseline": len(baseline_tags),
            "candidate": len(candidate_tags),
            "match": len(baseline_tags) == len(candidate_tags),
        },
        "genres_values": {
            "baseline": baseline_tags,
            "candidate": candidate_tags,
            "match": baseline_tags == candidate_tags,
        },
        "top_1_genre": {
            "baseline": baseline_tags[0] if baseline_tags else None,
            "candidate": candidate_tags[0] if candidate_tags else None,
            "match": bool(baseline_tags and candidate_tags and baseline_tags[0] == candidate_tags[0]),
        },
        "top_n_overlap": {
            "count": len(shared),
            "baseline_count": len(baseline_tags),
            "candidate_count": len(candidate_tags),
            "values": shared,
        },
        "genres_pretty": {
            "baseline": genres_pretty(baseline_payload),
            "candidate": genres_pretty(candidate_payload),
            "match": genres_pretty(baseline_payload) == genres_pretty(candidate_payload),
        },
        "scores_by_genre": {
            "baseline": genre_scores(baseline_payload),
            "candidate": genre_scores(candidate_payload),
        },
    }


def discover_names(baseline_dir: Path, candidate_dir: Path) -> List[str]:
    names = set()
    for directory in (baseline_dir, candidate_dir):
        for path in directory.glob("*.body.json"):
            names.add(path.name[: -len(".body.json")])
    return sorted(names)


def render_markdown(results: List[Dict[str, Any]]) -> str:
    lines = [
        "# Roadmap 3.5 Runtime Parity Comparison",
        "",
        "| Request | HTTP status | JSON parse | Keys match | Shape issues | Genres length | Top-1 | Top-N overlap | genres_pretty |",
        "|---|---:|---|---|---|---:|---|---:|---|",
    ]
    for result in results:
        status = result["http_status"]
        parse = result["json_parseability"]
        shape = result["shape_issues"]
        top_1 = result["top_1_genre"]
        overlap_data = result["top_n_overlap"]
        shape_text = "none"
        if shape["baseline"] or shape["candidate"]:
            shape_text = "baseline: {}; candidate: {}".format(
                ", ".join(shape["baseline"]) or "none",
                ", ".join(shape["candidate"]) or "none",
            )
        lines.append(
            "| {name} | {baseline}/{candidate} | {parse_ok} | {keys} | {shape} | {blen}/{clen} | {btop}/{ctop} | {overlap} | {pretty} |".format(
                name=result["name"],
                baseline=status["baseline"],
                candidate=status["candidate"],
                parse_ok="yes" if parse["baseline_ok"] and parse["candidate_ok"] else "no",
                keys="yes" if result["top_level_keys"]["match"] else "no",
                shape=shape_text.replace("|", "\\|"),
                blen=result["genres_length"]["baseline"],
                clen=result["genres_length"]["candidate"],
                btop=top_1["baseline"],
                ctop=top_1["candidate"],
                overlap=overlap_data["count"],
                pretty="yes" if result["genres_pretty"]["match"] else "no",
            )
        )
    lines.extend(["", "```json", json.dumps(results, ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-dir", required=True, type=Path)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--name", action="append", help="Request name without .body.json suffix. May be repeated.")
    args = parser.parse_args()

    names = args.name or discover_names(args.baseline_dir, args.candidate_dir)
    results = [compare_pair(name, args.baseline_dir, args.candidate_dir) for name in names]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(results), encoding="utf-8")
    print(f"wrote comparison: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
