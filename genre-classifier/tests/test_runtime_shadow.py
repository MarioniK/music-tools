import asyncio

import pytest

from app.services import runtime_shadow
from app.services.runtime_shadow import run_shadow_observer


@pytest.mark.asyncio
async def test_runtime_shadow_skips_when_disabled_by_config():
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=False,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
    )

    assert calls == []
    assert outcome.status == "skipped_by_config"
    assert outcome.comparison is None
    assert outcome.shadow_tags == []


@pytest.mark.asyncio
async def test_runtime_shadow_skips_when_sample_rate_zero():
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=0.0,
        shadow_timeout_seconds=1.0,
    )

    assert calls == []
    assert outcome.status == "skipped_by_sampling"


@pytest.mark.asyncio
async def test_runtime_shadow_deterministic_sampling_skip():
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=0.5,
        shadow_timeout_seconds=1.0,
        random_value=0.7,
    )

    assert calls == []
    assert outcome.status == "skipped_by_sampling"


@pytest.mark.asyncio
async def test_runtime_shadow_deterministic_sampling_run():
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=0.5,
        shadow_timeout_seconds=1.0,
        random_value=0.2,
    )

    assert calls == ["called"]
    assert outcome.status == "success"


@pytest.mark.asyncio
async def test_runtime_shadow_sample_rate_one_always_runs():
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
        random_value=0.99,
    )

    assert calls == ["called"]
    assert outcome.status == "success"


@pytest.mark.asyncio
async def test_runtime_shadow_successful_comparison():
    async def shadow_runner():
        return ["rock", "indie"]

    outcome = await run_shadow_observer(
        legacy_tags=["rock", "alternative"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
    )

    assert outcome.status == "success"
    assert outcome.shadow_tags == ["rock", "indie"]
    assert outcome.comparison.shared_tags == ["rock"]
    assert outcome.comparison.weak_overlap is True
    assert outcome.comparison.has_partial_overlap is True


@pytest.mark.asyncio
async def test_runtime_shadow_timeout_isolated():
    async def shadow_runner():
        await asyncio.sleep(0.05)
        return ["rock"]

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=0.001,
    )

    assert outcome.status == "timeout"
    assert outcome.comparison is None
    assert outcome.shadow_tags == []


@pytest.mark.asyncio
async def test_runtime_shadow_provider_error_isolated():
    async def shadow_runner():
        raise RuntimeError("provider failed loudly")

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
    )

    assert outcome.status == "provider_error"
    assert outcome.error_type == "RuntimeError"
    assert outcome.error_message == "provider failed loudly"


@pytest.mark.asyncio
async def test_runtime_shadow_invalid_output_none():
    async def shadow_runner():
        return None

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
    )

    assert outcome.status == "invalid_output"


@pytest.mark.asyncio
async def test_runtime_shadow_invalid_output_plain_string():
    async def shadow_runner():
        return "rock"

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
    )

    assert outcome.status == "invalid_output"


@pytest.mark.asyncio
async def test_runtime_shadow_invalid_output_list_with_non_string():
    async def shadow_runner():
        return ["rock", 1]

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
    )

    assert outcome.status == "invalid_output"


@pytest.mark.asyncio
async def test_runtime_shadow_comparison_error_isolated(monkeypatch):
    async def shadow_runner():
        return ["rock"]

    def raise_comparison_error(legacy_tags, shadow_tags):
        raise RuntimeError("comparison failed")

    monkeypatch.setattr(
        runtime_shadow,
        "compare_shadow_tags",
        raise_comparison_error,
    )

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
    )

    assert outcome.status == "comparison_error"
    assert outcome.error_type == "RuntimeError"
    assert outcome.error_message == "comparison failed"


@pytest.mark.asyncio
async def test_runtime_shadow_does_not_mutate_production_response():
    production_response = {
        "genres": [{"tag": "rock", "score": 0.9}],
        "provider": "legacy_musicnn",
    }
    original_response = {
        "genres": [{"tag": "rock", "score": 0.9}],
        "provider": "legacy_musicnn",
    }

    async def shadow_runner():
        return ["electronic"]

    outcome = await run_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        shadow_enabled=True,
        shadow_sample_rate=1.0,
        shadow_timeout_seconds=1.0,
    )

    assert outcome.status == "success"
    assert production_response == original_response
