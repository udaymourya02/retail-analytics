"""
logger.py
=========
Centralised logging for the ETL pipeline.
Uses loguru for structured, coloured console output and file rotation.
"""

import sys
from loguru import logger

# Remove default loguru handler
logger.remove()

# Console: human-readable coloured output
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
           "<level>{message}</level>",
    level="INFO",
    colorize=True,
)

# File: full debug log, rotated daily
logger.add(
    "logs/pipeline_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
    level="DEBUG",
    rotation="00:00",   # new file at midnight
    retention="30 days",
    compression="zip",
)

__all__ = ["logger"]
