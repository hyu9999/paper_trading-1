from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import settings
from app.api import router
from app.core.event import create_start_app_handler, create_stop_app_handler

app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", create_start_app_handler(app))
app.add_event_handler("shutdown", create_stop_app_handler(app))

app.include_router(router, prefix=settings.api_prefix)
