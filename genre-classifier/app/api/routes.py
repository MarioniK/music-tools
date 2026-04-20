from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from app.services.classify import classify_upload


router = APIRouter()


def _templates(request: Request):
    return request.app.state.templates


@router.get("/")
def index(request: Request):
    return _templates(request).TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": None,
            "error": None,
        },
    )


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/classify")
async def classify(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        genres, normalized = await classify_upload(file_bytes, file.filename or "")
    except Exception as e:
        return JSONResponse(
            {
                "ok": False,
                "error": str(e),
            },
            status_code=400,
        )

    return {
        "ok": True,
        "message": "Аудио проанализировано",
        "genres": genres,
        "genres_pretty": normalized,
    }


@router.post("/classify-form")
async def classify_form(request: Request, file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        genres, normalized = await classify_upload(file_bytes, file.filename or "")
    except Exception as e:
        return _templates(request).TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "error": str(e),
            },
            status_code=400,
        )

    result = {
        "message": "Аудио проанализировано",
        "genres": genres,
        "genres_pretty": normalized,
    }

    return _templates(request).TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result,
            "error": None,
        },
    )
