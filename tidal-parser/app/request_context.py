from contextvars import ContextVar
from uuid import uuid4


_current_request_id: ContextVar[str] = ContextVar("current_request_id", default="-")


def generate_request_id():
    return uuid4().hex


def set_current_request_id(request_id: str):
    return _current_request_id.set(request_id)


def get_current_request_id():
    return _current_request_id.get()


def reset_current_request_id(token):
    _current_request_id.reset(token)
