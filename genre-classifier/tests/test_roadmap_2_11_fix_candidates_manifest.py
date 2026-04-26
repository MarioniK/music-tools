import json
from pathlib import Path


MANIFEST_PATH = Path("evaluation/manifests/roadmap_2_11/fix_candidates_v1.json")

REQUIRED_TOP_LEVEL_FIELDS = {
    "roadmap",
    "stage",
    "source_artifacts",
    "review_notes",
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

ALLOWED_CANDIDATE_TYPES = {
    "alias_normalization",
    "controlled_vocabulary",
    "threshold_ranking",
    "weak_output_handling",
    "compatibility_mapping",
    "prompt_discipline",
}

ALLOWED_CANDIDATE_STATUSES = {"proposed", "deferred", "no_fix"}
ALLOWED_CANDIDATE_RISKS = {"low", "medium", "high"}


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
    assert isinstance(manifest["review_notes"], dict)
    assert isinstance(manifest["candidates"], list)


def test_roadmap_2_11_fix_candidates_have_required_fields_and_unique_ids_when_present():
    manifest = load_manifest()
    seen_ids = set()

    for candidate in manifest["candidates"]:
        assert REQUIRED_CANDIDATE_FIELDS <= set(candidate)
        assert candidate["id"] not in seen_ids
        assert candidate["type"] in ALLOWED_CANDIDATE_TYPES
        assert candidate["status"] in ALLOWED_CANDIDATE_STATUSES
        assert candidate["risk"] in ALLOWED_CANDIDATE_RISKS
        assert isinstance(candidate["evidence"], list)
        assert candidate["evidence"]
        seen_ids.add(candidate["id"])


def test_roadmap_2_11_empty_fix_candidates_manifest_explains_absence_of_candidates():
    manifest = load_manifest()

    if manifest["candidates"]:
        return

    review_notes = manifest["review_notes"]

    assert review_notes["reviewed_existing_files"]
    assert "No evidence-backed compatibility fix candidates were found." == review_notes[
        "candidate_decision"
    ]
    assert review_notes["no_candidates_reason"]
