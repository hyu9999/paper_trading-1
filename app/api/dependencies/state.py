from app import state
from app.services.engines.main_engine import MainEngine


async def get_engine() -> MainEngine:
    return state.engine
