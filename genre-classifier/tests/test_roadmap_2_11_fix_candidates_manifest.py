import json
from pathlib import Path


MANIFEST_PATH = Path("evaluation/manifests/roadmap_2_11/fix_candidates_v1.json")

REQUIRED_TOP_LEVEL_FIELDS = {
    "roadmap",
    "stage",
    "source_artifacts",
    "candidates",
}

REQUIRED_CANDIDATE_FIELDS = {
    "id",
    "type",
    "status",
    "risk",
    "category",
    "finding_summary",
    "evidence",
    "proposed_change",
    "why_now",
    "why_safe",
    "test_plan",
    "rollback",
    "notes",
}


def load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_roadmap_2_11_fix_candidates_manifest_exists_and_has_required_top_level_fields():
    assert MANIFEST_PATH.exists()

    manifest = load_manifest()

    assert REQUIRED_TOP_LEVEL_FIELDS <= set(manifest)
    assert manifest["roadmap"] == "2.11"
    assert manifest["stage"] == "curated_findings_review"
    assert isinstance(manifest["source_artifacts"], list)
    assert manifest["source_artifacts"]
    assert isinstance(manifest["candidates"], list)


def test_roadmap_2_11_fix_candidates_have_required_fields_and_unique_ids_when_present():
    manifest = load_manifest()
    seen_ids = set()

    for candidate in manifest["candidates"]:
        assert REQUIRED_CANDIDATE_FIELDS <= set(candidate)
        assert candidate["id"] not in seen_ids
        seen_ids.add(candidate["id"])
