import types
from pathlib import Path
from contextvars import ContextVar

from dynaconf import Dynaconf

ROOT_PATH = Path.cwd()
_app_state: ContextVar = ContextVar("_app_state", default=types.SimpleNamespace())

# 应用设置
settings = Dynaconf(
    settings_files=["app/settings.toml"],
    environments=True,
    load_dotenv=True,
    root_path=ROOT_PATH,
    dotenv_path=".env"
)

state = _app_state.get()
