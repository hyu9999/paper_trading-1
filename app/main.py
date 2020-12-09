from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import settings
from app.api import router
from app.core.events import start_app, stop_app
from app.exceptions.events import register_exceptions


def get_application() -> FastAPI:

    application = FastAPI(
        title=settings.project_name,
        description=settings.description,
        version=settings.version,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_event_handler("startup", start_app)
    application.add_event_handler("startup", register_exceptions(application))
    application.add_event_handler("shutdown", stop_app)

    application.include_router(router, prefix=settings.api_prefix)

    return application


app = get_application()
