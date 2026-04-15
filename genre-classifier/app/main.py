import asyncio
from functools import partial
from pathlib import Path
import shutil
import subprocess
import json
import os
import tempfile
import logging

import numpy as np
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from essentia.standard import MonoLoader, TensorflowPredictMusiCNN
from app.genre_normalization import normalize_audio_prediction_genres


MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR / "tmp"
MODELS_DIR = BASE_DIR / "models"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

MODEL_PB = MODELS_DIR / "msd-musicnn-1.pb"
MODEL_JSON = MODELS_DIR / "msd-musicnn-1.json"

TMP_DIR.mkdir(exist_ok=True)

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
logger = logging.getLogger("genre_classifier")

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )


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
    if not MODEL_PB.exists():
        raise RuntimeError(f"Файл модели не найден: {MODEL_PB}")

    if not MODEL_JSON.exists():
        raise RuntimeError(f"Файл metadata не найден: {MODEL_JSON}")

    with open(MODEL_JSON, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    classes = metadata.get("classes")
    if not classes:
        raise RuntimeError("В metadata модели нет списка classes")

    audio = MonoLoader(
        filename=str(wav_path),
        sampleRate=16000
    )()

    activations = TensorflowPredictMusiCNN(
        graphFilename=str(MODEL_PB)
    )(audio)

    mean_scores = np.mean(activations, axis=0)

    pairs = []

    for label, score in zip(classes, mean_scores):
        pairs.append({
            "tag": str(label).lower(),
            "prob": round(float(score), 4)
        })

    pairs.sort(key=lambda x: x["prob"], reverse=True)
    return pairs[:8]


def normalize_genres(raw_genres):
    return normalize_audio_prediction_genres(raw_genres, min_prob=0.05)


def validate_upload(file_bytes: bytes, filename: str):
    if not file_bytes:
        raise RuntimeError("Файл пустой")

    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise RuntimeError("Файл слишком большой. Максимальный размер — 20 МБ")

    suffix = Path(filename or "").suffix.lower()
    allowed = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}

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
        file_size
    )

    try:
        validate_upload(file_bytes, safe_filename)
    except Exception as e:
        logger.warning(
            "event=validation_error filename=%s size_bytes=%d error=%s",
            safe_filename,
            file_size,
            str(e)
        )
        raise

    suffix = Path(filename or "").suffix.lower() or ".bin"

    upload_path = None
    wav_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=str(TMP_DIR)) as tmp_upload:
            tmp_upload.write(file_bytes)
            upload_path = Path(tmp_upload.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=str(TMP_DIR)) as tmp_wav:
            wav_path = Path(tmp_wav.name)

        try:
            normalize_audio_file(upload_path, wav_path)
        except Exception as e:
            logger.error(
                "event=ffmpeg_error filename=%s size_bytes=%d error=%s",
                safe_filename,
                file_size,
                str(e)
            )
            raise

        genres = run_genre_classification(wav_path)
        normalized = normalize_genres(genres)
        logger.info(
            "event=file_processing_succeeded filename=%s size_bytes=%d",
            safe_filename,
            file_size
        )
        return genres, normalized
    finally:
        cleanup_file(upload_path)
        cleanup_file(wav_path)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": None,
            "error": None
        }
    )


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/classify")
async def classify(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        loop = asyncio.get_event_loop()
        genres, normalized = await loop.run_in_executor(
            None,
            partial(process_uploaded_audio, file_bytes, file.filename or ""),
        )
    except Exception as e:
        return JSONResponse(
            {
                "ok": False,
                "error": str(e)
            },
            status_code=400
        )

    return {
        "ok": True,
        "message": "Аудио проанализировано",
        "genres": genres,
        "genres_pretty": normalized
    }


@app.post("/classify-form")
async def classify_form(request: Request, file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        loop = asyncio.get_event_loop()
        genres, normalized = await loop.run_in_executor(
            None,
            partial(process_uploaded_audio, file_bytes, file.filename or ""),
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "error": str(e)
            },
            status_code=400
        )

    result = {
        "message": "Аудио проанализировано",
        "genres": genres,
        "genres_pretty": normalized
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result,
            "error": None
        }
    )
