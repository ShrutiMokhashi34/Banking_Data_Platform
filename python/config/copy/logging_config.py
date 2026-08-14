"""
===============================================================================
Banking Data Platform
logging_config.py

Centralized logging configuration.

Author : Shruti Mokhashi
===============================================================================
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.config import LOG_DIR, LOG_FILE, LOG_LEVEL


def setup_logger(logger_name: str = "banking_data_platform") -> logging.Logger:
    """
    Configure and return the application logger.

    Parameters
    ----------
    logger_name : str
        Name of the logger.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """

    # Create log directory if it doesn't exist
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(logger_name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Rotating File Handler
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger