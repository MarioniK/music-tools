import pytest
from starlette.requests import Request
from starlette.responses import Response

from app import main
from app import request_context
from app.pipeline_logging import logger


def _make_request(path="/api/parse"):
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    }
    return Request(scope)


async def _run_middleware(request, call_next):
    return await main.request_correlation_middleware(request, call_next)


@pytest.mark.asyncio
async def test_request_middleware_adds_x_request_id_and_state(monkeypatch):
    request = _make_request()
    monkeypatch.setattr(request_context, "generate_request_id", lambda: "req-1")

    async def call_next(inner_request):
        assert inner_request.state.request_id == "req-1"
        return Response("ok", status_code=200)

    response = await _run_middleware(request, call_next)

    assert response.headers["X-Request-ID"] == "req-1"
    assert request_context.get_current_request_id() == "-"


@pytest.mark.asyncio
async def test_app_log_inside_request_context_contains_request_id(monkeypatch, caplog):
    request = _make_request()
    monkeypatch.setattr(request_context, "generate_request_id", lambda: "req-log")

    async def call_next(inner_request):
        logger.info("event=test_log outcome=success")
        return Response("ok", status_code=200)

    with caplog.at_level("INFO", logger="tidal_parser"):
        response = await _run_middleware(request, call_next)

    assert response.headers["X-Request-ID"] == "req-log"
    assert "request_id=req-log event=test_log outcome=success" in caplog.text


def test_log_outside_request_context_uses_neutral_request_id(caplog):
    with caplog.at_level("INFO", logger="tidal_parser"):
        logger.info("event=outside_context outcome=success")

    assert "request_id=- event=outside_context outcome=success" in caplog.text


@pytest.mark.asyncio
async def test_request_context_does_not_leak_between_requests(monkeypatch, caplog):
    request_a = _make_request("/api/parse")
    request_b = _make_request("/clear-cache")
    request_ids = iter(["req-a", "req-b"])
    monkeypatch.setattr(request_context, "generate_request_id", lambda: next(request_ids))

    async def call_next(inner_request):
        logger.info("event=test_log path=%s outcome=success", inner_request.url.path)
        return Response("ok", status_code=200)

    with caplog.at_level("INFO", logger="tidal_parser"):
        response_a = await _run_middleware(request_a, call_next)
        response_b = await _run_middleware(request_b, call_next)

    assert response_a.headers["X-Request-ID"] == "req-a"
    assert response_b.headers["X-Request-ID"] == "req-b"
    assert "request_id=req-a event=test_log path=/api/parse outcome=success" in caplog.text
    assert "request_id=req-b event=test_log path=/clear-cache outcome=success" in caplog.text
    assert request_context.get_current_request_id() == "-"
