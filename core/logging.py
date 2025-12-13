"""Logging configuration using loguru.

Sets up structured logging to stdout with a standard format.
"""

import sys

from loguru import logger

# Remove default handlers and reconfigure
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)
