from pathlib import Path
import shutil
import subprocess
import json
import os
import tempfile

import numpy as np
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from essentia.standard import MonoLoader, TensorflowPredictMusiCNN


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
    # Смягчённая логика:
    # - не душим теги слишком рано
    # - собираем полезные комбинации
    # - сохраняем больше исходной информации для tidal-parser
    filtered = [g for g in raw_genres if g.get("prob", 0) >= 0.05]

    tags = [str(g["tag"]).lower() for g in filtered if g.get("tag")]
    tag_set = set(tags)

    result = []

    def add(tag):
        if tag and tag not in result:
            result.append(tag)

    # Комбинации
    if "indie rock" in tag_set:
        add("indie rock")
    elif "indie" in tag_set and "rock" in tag_set:
        add("indie rock")

    if "experimental rock" in tag_set:
        add("experimental rock")
    elif "experimental" in tag_set and "rock" in tag_set:
        add("experimental rock")

    if "jazz rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "rock" in tag_set:
        add("jazz rock")
    elif "jazz" in tag_set and "instrumental" in tag_set and "experimental" in tag_set:
        add("avant-jazz")

    if "alternative rock" in tag_set:
        add("alternative rock")
    elif "alternative" in tag_set and "rock" in tag_set:
        add("alternative rock")

    if "instrumental rock" in tag_set:
        add("instrumental rock")
    elif "instrumental" in tag_set and "rock" in tag_set:
        add("instrumental rock")

    if "electronic" in tag_set:
        add("electronic")

    # Сохраняем и исходные теги, чтобы не обеднять результат
    for item in filtered:
        add(str(item["tag"]).lower())

    return result[:8]


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
    validate_upload(file_bytes, file.filename or "")

    suffix = Path(file.filename or "").suffix.lower() or ".bin"

    upload_path = None
    wav_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=str(TMP_DIR)) as tmp_upload:
            tmp_upload.write(file_bytes)
            upload_path = Path(tmp_upload.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=str(TMP_DIR)) as tmp_wav:
            wav_path = Path(tmp_wav.name)

        normalize_audio_file(upload_path, wav_path)
        genres = run_genre_classification(wav_path)
        normalized = normalize_genres(genres)

    except Exception as e:
        return JSONResponse(
            {
                "ok": False,
                "error": str(e)
            },
            status_code=400
        )
    finally:
        cleanup_file(upload_path)
        cleanup_file(wav_path)

    return {
        "ok": True,
        "message": "Аудио проанализировано",
        "genres": genres,
        "genres_pretty": normalized
    }


@app.post("/classify-form")
async def classify_form(request: Request, file: UploadFile = File(...)):
    file_bytes = await file.read()

    upload_path = None
    wav_path = None

    try:
        validate_upload(file_bytes, file.filename or "")
        suffix = Path(file.filename or "").suffix.lower() or ".bin"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=str(TMP_DIR)) as tmp_upload:
            tmp_upload.write(file_bytes)
            upload_path = Path(tmp_upload.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=str(TMP_DIR)) as tmp_wav:
            wav_path = Path(tmp_wav.name)

        normalize_audio_file(upload_path, wav_path)
        genres = run_genre_classification(wav_path)
        normalized = normalize_genres(genres)

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
    finally:
        cleanup_file(upload_path)
        cleanup_file(wav_path)

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