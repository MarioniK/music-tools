import json
from pathlib import Path


MANIFEST_DIR = Path("evaluation/manifests/roadmap_2_10")

MANIFESTS = {
    "curated_v1": MANIFEST_DIR / "curated_v1.json",
    "golden_v1": MANIFEST_DIR / "golden_v1.json",
    "repeat_run_v1": MANIFEST_DIR / "repeat_run_v1.json",
}

REQUIRED_TOP_LEVEL_FIELDS = {
    "manifest_version",
    "roadmap_stage",
    "subset_name",
    "description",
    "runtime_effect",
    "source_manifest",
    "entries",
}

REQUIRED_ENTRY_FIELDS = {
    "sample_id",
    "subset",
    "category",
    "difficulty",
    "notes",
    "input_ref",
}

ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}
ALLOWED_CATEGORIES = {
    "clear_single_genre",
    "contract_semantics",
    "genre_boundary",
    "ranking_stability",
}


def load_manifest(subset_name):
    return json.loads(MANIFESTS[subset_name].read_text(encoding="utf-8"))


def sample_ids(manifest):
    return {entry["sample_id"] for entry in manifest["entries"]}


def test_roadmap_2_10_manifests_are_valid_json_with_required_top_level_fields():
    for expected_subset, manifest_path in MANIFESTS.items():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert REQUIRED_TOP_LEVEL_FIELDS <= set(manifest)
        assert manifest["roadmap_stage"] == "2.10"
        assert manifest["runtime_effect"] == "none"
        assert manifest["subset_name"] == expected_subset
        assert isinstance(manifest["entries"], list)
        assert manifest["entries"]


def test_roadmap_2_10_manifest_entries_have_required_fields_and_allowed_values():
    for expected_subset in MANIFESTS:
        manifest = load_manifest(expected_subset)
        seen_sample_ids = set()

        for entry in manifest["entries"]:
            assert REQUIRED_ENTRY_FIELDS <= set(entry)
            assert entry["sample_id"] not in seen_sample_ids
            assert entry["subset"] == expected_subset
            assert entry["difficulty"] in ALLOWED_DIFFICULTIES
            assert entry["category"] in ALLOWED_CATEGORIES
            assert isinstance(entry["input_ref"], str)
            assert entry["input_ref"]

            seen_sample_ids.add(entry["sample_id"])


def test_roadmap_2_10_strict_subsets_are_curated_sample_id_subsets():
    curated_ids = sample_ids(load_manifest("curated_v1"))

    assert sample_ids(load_manifest("golden_v1")) <= curated_ids
    assert sample_ids(load_manifest("repeat_run_v1")) <= curated_ids
