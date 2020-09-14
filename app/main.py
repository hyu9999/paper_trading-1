from fastapi import FastAPI

from app import settings
from app.api import router
from app.core.events import create_start_app_handler, create_stop_app_handler


app = FastAPI(title=settings.project_name, description=settings.description, version=settings.version)

app.add_event_handler("startup", create_start_app_handler(app))
app.add_event_handler("shutdown", create_stop_app_handler(app))

app.include_router(router, prefix=settings.api_prefix)
