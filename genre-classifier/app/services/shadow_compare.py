from dataclasses import asdict, dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ShadowComparison:
    shared_tags: List[str]
    legacy_only_tags: List[str]
    llm_only_tags: List[str]
    shared_tag_count: int
    legacy_tag_count: int
    llm_tag_count: int
    top_tag_match: bool
    top_tag_mismatch: bool
    has_no_shared_tags: bool
    has_partial_overlap: bool
    weak_overlap: bool
    comparison_signal: str

    def to_dict(self):
        return asdict(self)


def compare_shadow_tags(legacy_tags: Iterable[str], llm_tags: Iterable[str]) -> ShadowComparison:
    """Compare provider tag lists for diagnostics only; never for production decisions."""
    normalized_legacy_tags = normalize_shadow_tags(legacy_tags)
    normalized_llm_tags = normalize_shadow_tags(llm_tags)

    legacy_tag_set = set(normalized_legacy_tags)
    llm_tag_set = set(normalized_llm_tags)

    shared_tags = [tag for tag in normalized_legacy_tags if tag in llm_tag_set]
    legacy_only_tags = [tag for tag in normalized_legacy_tags if tag not in llm_tag_set]
    llm_only_tags = [tag for tag in normalized_llm_tags if tag not in legacy_tag_set]

    shared_tag_count = len(shared_tags)
    legacy_tag_count = len(normalized_legacy_tags)
    llm_tag_count = len(normalized_llm_tags)

    both_have_tags = legacy_tag_count > 0 and llm_tag_count > 0
    top_tag_match = both_have_tags and normalized_legacy_tags[0] == normalized_llm_tags[0]
    top_tag_mismatch = both_have_tags and normalized_legacy_tags[0] != normalized_llm_tags[0]
    has_no_shared_tags = both_have_tags and shared_tag_count == 0
    has_partial_overlap = (
        shared_tag_count > 0
        and normalized_legacy_tags != normalized_llm_tags
    )
    weak_overlap = shared_tag_count == 1 and (
        legacy_tag_count > 1
        or llm_tag_count > 1
    )

    return ShadowComparison(
        shared_tags=shared_tags,
        legacy_only_tags=legacy_only_tags,
        llm_only_tags=llm_only_tags,
        shared_tag_count=shared_tag_count,
        legacy_tag_count=legacy_tag_count,
        llm_tag_count=llm_tag_count,
        top_tag_match=top_tag_match,
        top_tag_mismatch=top_tag_mismatch,
        has_no_shared_tags=has_no_shared_tags,
        has_partial_overlap=has_partial_overlap,
        weak_overlap=weak_overlap,
        comparison_signal=_get_comparison_signal(
            normalized_legacy_tags=normalized_legacy_tags,
            normalized_llm_tags=normalized_llm_tags,
            top_tag_match=top_tag_match,
            has_no_shared_tags=has_no_shared_tags,
            weak_overlap=weak_overlap,
            shared_tag_count=shared_tag_count,
        ),
    )


def normalize_shadow_tags(tags: Iterable[str]) -> List[str]:
    """Normalize diagnostic comparison tags without changing compatibility mappings."""
    normalized_tags = []
    seen_tags = set()

    for tag in tags or []:
        normalized_tag = " ".join(str(tag or "").strip().lower().split())
        if not normalized_tag or normalized_tag in seen_tags:
            continue

        seen_tags.add(normalized_tag)
        normalized_tags.append(normalized_tag)

    return normalized_tags


def _get_comparison_signal(
    normalized_legacy_tags,
    normalized_llm_tags,
    top_tag_match: bool,
    has_no_shared_tags: bool,
    weak_overlap: bool,
    shared_tag_count: int,
) -> str:
    if not normalized_legacy_tags and not normalized_llm_tags:
        return "both_empty"

    if normalized_legacy_tags and not normalized_llm_tags:
        return "legacy_only"

    if normalized_llm_tags and not normalized_legacy_tags:
        return "llm_only"

    if normalized_legacy_tags == normalized_llm_tags:
        return "exact_match"

    if has_no_shared_tags:
        return "no_shared_tags"

    if weak_overlap:
        return "weak_overlap"

    if top_tag_match:
        return "top_tag_match"

    if shared_tag_count > 0:
        return "partial_overlap"

    return "no_shared_tags"
