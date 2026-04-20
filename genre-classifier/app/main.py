import logging

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.core import settings
from app.services.classify import validate_upload

logger = logging.getLogger("genre_classifier")
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

from app.api.routes import router


def create_app():
    app = FastAPI()
    app.mount(
        "/static",
        StaticFiles(directory=settings.STATIC_DIR),
        name="static",
    )
    app.state.templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
    app.include_router(router)
    return app


app = create_app()
