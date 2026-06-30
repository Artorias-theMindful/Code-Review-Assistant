from fastapi import FastAPI

from app.api.router import api_router
from app.core.logging import configure_logging
from app.exceptions import register_exception_handlers
from app.middleware import register_middlewares
from app.config import settings


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.project_name,
        description="Upload git diffs or PR patch files and get parsed metadata back.",
        version=settings.version,
    )

    register_exception_handlers(app)
    register_middlewares(app)
    app.include_router(api_router)

    return app


app = create_app()
