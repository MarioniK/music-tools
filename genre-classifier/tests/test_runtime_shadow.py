import asyncio

import pytest

from app.services import runtime_shadow
from app.services.runtime_shadow import run_configured_shadow_observer, run_shadow_observer


@pytest.fixture(autouse=True)
def reset_shadow_runtime_state(monkeypatch):
    runtime_shadow._active_shadow_executions = 0
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_ENABLED", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT", raising=False)


def enable_shadow_runtime(monkeypatch, *, sample_rate="1.0", timeout="1.0", max_concurrent="1"):
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_ENABLED", "true")
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_SAMPLE_RATE", sample_rate)
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_TIMEOUT_SECONDS", timeout)
    monkeypatch.setenv("GENRE_CLASSIFIER_SHADOW_MAX_CONCURRENT", max_concurrent)


@pytest.mark.asyncio
async def test_configured_runtime_shadow_disabled_config_skips_observer():
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
    )

    assert calls == []
    assert outcome.status == "skipped_by_config"


@pytest.mark.asyncio
async def test_configured_runtime_shadow_sample_rate_zero_skips_observer(monkeypatch):
    enable_shadow_runtime(monkeypatch, sample_rate="0.0")
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
    )

    assert calls == []
    assert outcome.status == "skipped_by_sampling"


@pytest.mark.asyncio
async def test_configured_runtime_shadow_sample_rate_one_calls_observer(monkeypatch):
    enable_shadow_runtime(monkeypatch, sample_rate="1.0")
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
    )

    assert calls == ["called"]
    assert outcome.status == "success"


@pytest.mark.asyncio
async def test_configured_runtime_shadow_probabilistic_sampling_skips_observer(monkeypatch):
    enable_shadow_runtime(monkeypatch, sample_rate="0.5")
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        random_value=0.7,
    )

    assert calls == []
    assert outcome.status == "skipped_by_sampling"


@pytest.mark.asyncio
async def test_configured_runtime_shadow_probabilistic_sampling_calls_observer(monkeypatch):
    enable_shadow_runtime(monkeypatch, sample_rate="0.5")
    calls = []

    async def shadow_runner():
        calls.append("called")
        return ["rock"]

    outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
        random_value=0.2,
    )

    assert calls == ["called"]
    assert outcome.status == "success"


@pytest.mark.asyncio
async def test_configured_runtime_shadow_observer_exception_is_swallowed(monkeypatch):
    enable_shadow_runtime(monkeypatch)

    async def shadow_runner():
        raise RuntimeError("shadow failed")

    outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
    )

    assert outcome.status == "provider_error"
    assert outcome.error_type == "RuntimeError"


@pytest.mark.asyncio
async def test_configured_runtime_shadow_timeout_is_swallowed(monkeypatch):
    enable_shadow_runtime(monkeypatch, timeout="0.001")

    async def shadow_runner():
        await asyncio.sleep(0.05)
        return ["rock"]

    outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
    )

    assert outcome.status == "timeout"
    assert outcome.comparison is None
    assert outcome.shadow_tags == []


@pytest.mark.asyncio
async def test_configured_runtime_shadow_concurrency_saturation_skips_without_queueing(monkeypatch):
    enable_shadow_runtime(monkeypatch, max_concurrent="1")
    started = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def slow_shadow_runner():
        calls.append("slow")
        started.set()
        await release.wait()
        return ["rock"]

    async def saturated_shadow_runner():
        calls.append("saturated")
        return ["rock"]

    first_task = asyncio.create_task(
        run_configured_shadow_observer(
            legacy_tags=["rock"],
            shadow_runner=slow_shadow_runner,
        )
    )
    await started.wait()

    saturated_outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=saturated_shadow_runner,
    )

    release.set()
    first_outcome = await first_task

    assert calls == ["slow"]
    assert saturated_outcome.status == "skipped_by_concurrency"
    assert first_outcome.status == "success"


@pytest.mark.asyncio
async def test_configured_runtime_shadow_does_not_mutate_production_response(monkeypatch):
    enable_shadow_runtime(monkeypatch)
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

    outcome = await run_configured_shadow_observer(
        legacy_tags=["rock"],
        shadow_runner=shadow_runner,
    )

    assert outcome.status == "success"
    assert production_response == original_response


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
