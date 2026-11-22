import pytest

from app import main


def _make_request(method="POST", path="/", request_id=None):
    request = main.Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 12345),
            "scheme": "http",
        }
    )
    if request_id is not None:
        request.state.request_id = request_id
    return request


@pytest.fixture
def post_form():
    """POST `/` без rate-limit обёртки: `await post_form(url, request_id=None, manual_release_type=None, audio=None)`."""
    handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    async def _post(url, request_id=None, manual_release_type=None, audio=None):
        kwargs = {}
        if manual_release_type is not None:
            kwargs["manual_release_type"] = manual_release_type
        return await handler(
            _make_request(request_id=request_id),
            url=url,
            force_refresh="0",
            audio=audio,
            **kwargs,
        )

    return _post


@pytest.fixture
def get_api():
    """GET `/api/parse` без rate-limit обёртки: `await get_api(url, request_id=None)`."""
    handler = getattr(main.parse_api, "__wrapped__", main.parse_api)

    async def _get(url, request_id=None):
        return await handler(
            _make_request(method="GET", path="/api/parse", request_id=request_id),
            url=url,
            force_refresh=0,
        )

    return _get
