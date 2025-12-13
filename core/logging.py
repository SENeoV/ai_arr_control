"""Logging configuration using loguru.

Sets up structured, professional logging to stdout with a standard format.
Supports debug mode for verbose output and can be extended with file logging.
"""

import sys
from typing import Optional

from loguru import logger

# Remove default handlers and reconfigure
logger.remove()

# Standard production log format
LOG_FORMAT = (
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Add console output with color support
logger.add(
    sys.stdout,
    level="INFO",
    format=LOG_FORMAT,
    colorize=True,
)


def configure_debug_logging(enabled: bool = False) -> None:
    """Configure debug-level logging if enabled.
    
    Args:
        enabled: If True, sets log level to DEBUG for verbose output
    """
    if enabled:
        logger.remove()
        logger.add(
            sys.stdout,
            level="DEBUG",
            format=LOG_FORMAT,
            colorize=True,
        )


def add_file_logging(file_path: str, level: str = "INFO") -> None:
    """Add file-based logging in addition to console output.
    
    Args:
        file_path: Path where log file should be written
        level: Minimum log level for file output
    """
    logger.add(
        file_path,
        level=level,
        format=LOG_FORMAT.replace("<level>", "").replace("</level>", ""),
        colorize=False,
        rotation="500 MB",  # Rotate when file reaches 500MB
        retention="7 days",  # Keep logs for 7 days
    )
