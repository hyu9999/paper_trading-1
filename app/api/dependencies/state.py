from starlette.requests import Request

from app.services.engines.main_engine import MainEngine


async def get_engine(request: Request) -> MainEngine:
    return request.app.state.engine
