"""Logging configuration with rich."""

import logging

from rich.console import Console
from rich.logging import RichHandler

console = Console()

LOG_FORMAT = "%(message)s"
DATE_FORMAT = "[%x]"


def setup_logging(level: str = "INFO", rich_handler: bool = True) -> logging.Logger:
    """Configure logging with optional RichHandler.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rich_handler: Whether to use RichHandler for rich output

    Returns:
        Configured logger
    """
    logger = logging.getLogger("bill_extract")
    logger.setLevel(getattr(logging, level.upper()))

    if rich_handler:
        handler = RichHandler(
            console=console,
            markup=True,
            show_time=False,
            show_path=False,
        )
    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    logger.propagate = False

    return logger


def get_logger(name: str = "bill_extract") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
