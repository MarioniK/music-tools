import asyncio
import json
import logging
import subprocess
import tempfile
from functools import partial
from pathlib import Path

import numpy as np
from essentia.standard import MonoLoader, TensorflowPredictMusiCNN

from app.core import settings
from app.providers.compat import (
    map_validated_result_to_legacy_genres,
    map_validated_result_to_legacy_genres_pretty,
)
from app.providers.factory import get_genre_provider
from app.providers.validation import validate_and_normalize_provider_result


logger = logging.getLogger("genre_classifier")


def normalize_audio_file(input_path: Path, output_path: Path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"ffmpeg не смог обработать файл:\n{stderr}")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("ffmpeg завершился без ошибки, но нормализованный WAV не был создан")


def run_genre_classification(wav_path: Path):
    if not settings.MODEL_PB.exists():
        raise RuntimeError(f"Файл модели не найден: {settings.MODEL_PB}")

    if not settings.MODEL_JSON.exists():
        raise RuntimeError(f"Файл metadata не найден: {settings.MODEL_JSON}")

    with open(settings.MODEL_JSON, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    classes = metadata.get("classes")
    if not classes:
        raise RuntimeError("В metadata модели нет списка classes")

    audio = MonoLoader(
        filename=str(wav_path),
        sampleRate=16000,
    )()

    activations = TensorflowPredictMusiCNN(
        graphFilename=str(settings.MODEL_PB)
    )(audio)

    mean_scores = np.mean(activations, axis=0)

    pairs = []

    for label, score in zip(classes, mean_scores):
        pairs.append({
            "tag": str(label).lower(),
            "prob": round(float(score), 4),
        })

    pairs.sort(key=lambda x: x["prob"], reverse=True)
    return pairs[:8]


def validate_upload(file_bytes: bytes, filename: str):
    if not file_bytes:
        raise RuntimeError("Файл пустой")

    if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
        raise RuntimeError("Файл слишком большой. Максимальный размер — 20 МБ")

    suffix = Path(filename or "").suffix.lower()
    allowed = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}

    if not suffix:
        raise RuntimeError("У файла должно быть расширение")

    if suffix and suffix not in allowed:
        raise RuntimeError("Неподдерживаемый формат файла")


def cleanup_file(path):
    if not path:
        return
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


def process_uploaded_audio(file_bytes: bytes, filename: str):
    safe_filename = filename or ""
    file_size = len(file_bytes)
    logger.info(
        "event=file_processing_started filename=%s size_bytes=%d",
        safe_filename,
        file_size,
    )

    try:
        validate_upload(file_bytes, safe_filename)
    except Exception as e:
        logger.warning(
            "event=validation_error filename=%s size_bytes=%d error=%s",
            safe_filename,
            file_size,
            str(e),
        )
        raise

    suffix = Path(filename or "").suffix.lower() or ".bin"

    upload_path = None
    wav_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=str(settings.TMP_DIR)) as tmp_upload:
            tmp_upload.write(file_bytes)
            upload_path = Path(tmp_upload.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=str(settings.TMP_DIR)) as tmp_wav:
            wav_path = Path(tmp_wav.name)

        try:
            normalize_audio_file(upload_path, wav_path)
        except Exception as e:
            logger.error(
                "event=ffmpeg_error filename=%s size_bytes=%d error=%s",
                safe_filename,
                file_size,
                str(e),
            )
            raise

        provider = get_genre_provider(settings)
        provider_result = provider.classify(str(wav_path))
        validated_result = validate_and_normalize_provider_result(provider_result)
        genres = map_validated_result_to_legacy_genres(validated_result)
        normalized = map_validated_result_to_legacy_genres_pretty(validated_result)
        logger.info(
            "event=file_processing_succeeded filename=%s size_bytes=%d",
            safe_filename,
            file_size,
        )
        return genres, normalized
    finally:
        cleanup_file(upload_path)
        cleanup_file(wav_path)


async def classify_upload(file_bytes: bytes, filename: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(process_uploaded_audio, file_bytes, filename or ""),
    )
