import pytest

from app import main


@pytest.fixture
def post_form():
    """POST `/` form handler без rate-limit обёртки: `await post_form(url)` -> response."""
    handler = getattr(main.parse_form, "__wrapped__", main.parse_form)

    async def _post(url):
        return await handler(
            main.Request(
                {
                    "type": "http",
                    "method": "POST",
                    "path": "/",
                    "headers": [],
                    "query_string": b"",
                    "server": ("testserver", 80),
                    "client": ("127.0.0.1", 12345),
                    "scheme": "http",
                }
            ),
            url=url,
            force_refresh="0",
            audio=None,
        )

    return _post
