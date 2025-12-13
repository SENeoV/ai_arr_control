from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>", level="INFO")

__all__ = ["logger"]
