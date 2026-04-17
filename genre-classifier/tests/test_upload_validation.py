import pytest
import sys
import types

if "numpy" not in sys.modules:
    numpy_stub = types.ModuleType("numpy")
    numpy_stub.mean = lambda *args, **kwargs: None
    sys.modules["numpy"] = numpy_stub

if "essentia" not in sys.modules:
    essentia_stub = types.ModuleType("essentia")
    essentia_standard_stub = types.ModuleType("essentia.standard")

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return []

    essentia_standard_stub.MonoLoader = _Dummy
    essentia_standard_stub.TensorflowPredictMusiCNN = _Dummy
    essentia_stub.standard = essentia_standard_stub
    sys.modules["essentia"] = essentia_stub
    sys.modules["essentia.standard"] = essentia_standard_stub

from app.main import validate_upload


def test_validate_upload_rejects_missing_extension():
    with pytest.raises(RuntimeError, match="У файла должно быть расширение"):
        validate_upload(b"audio-bytes", "track")


def test_validate_upload_accepts_supported_extension():
    validate_upload(b"audio-bytes", "track.mp3")


def test_validate_upload_rejects_unsupported_extension():
    with pytest.raises(RuntimeError, match="Неподдерживаемый формат файла"):
        validate_upload(b"audio-bytes", "track.exe")
