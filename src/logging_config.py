from loguru import logger
from .config import LOG_DIR
import os

os.makedirs(LOG_DIR, exist_ok=True)

if not getattr(logger, "_configured", False):
    logger.add(
        LOG_DIR / "stanza.log",
        rotation="1 week",
        level="INFO",
    )
    logger._configured = True