import logging
import sys
from pprint import pformat
from types import FrameType
from typing import cast

from loguru import logger
from loguru._defaults import LOGURU_FORMAT

from app import settings


class InterceptHandler(logging.Handler):
    def emit(self, record) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def format_record(record: dict) -> str:
    """
    Custom format for loguru loggers.
    Uses pformat for log any data like request/response body during debug.
    Works with logging if loguru handler it.
    """
    format_string = LOGURU_FORMAT

    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"], indent=4, compact=True, width=88
        )
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"
    return format_string


async def init_logger() -> None:
    """初始化logger"""
    logger.configure(
        handlers=[
            {"sink": sys.stdout, "level": settings.log.level, "format": format_record}
        ]
    )
    # 统一设置uvicorn的处理器为loguru
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logger.info("初始化日志管理器完成.")
