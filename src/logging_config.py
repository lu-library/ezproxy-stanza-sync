from loguru import logger
import os
from .config import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)

logger.add(
    LOG_DIR / "stanza.log",
    rotation="1 week",
    level="INFO",
)
