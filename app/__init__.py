from pathlib import Path

from dynaconf import Dynaconf


ROOT_PATH = Path.cwd()

# 应用设置
settings = Dynaconf(
    settings_files=["app/settings.toml"],
    environments=True,
    load_dotenv=True,
    root_path=ROOT_PATH,
    dotenv_path=".env"
)
