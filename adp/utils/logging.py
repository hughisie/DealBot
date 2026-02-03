"""Logging configuration for DealBot."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(level: int = logging.INFO, console: Optional[Console] = None) -> logging.Logger:
    """Configure logging with Rich handler and file handler."""
    if console is None:
        console = Console()

    # Create logs directory in user's home
    log_dir = Path.home() / "Library" / "Logs" / "DealBot"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "dealbot.log"

    # File handler for persistent logs
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # Configure root logger with both handlers
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                markup=True,
            ),
            file_handler,  # Add file handler
        ],
    )

    logger = logging.getLogger("dealbot")
    logger.setLevel(level)
    logger.info(f"Logging initialized. Log file: {log_file}")

    return logger


def get_logger(name: str = "dealbot") -> logging.Logger:
    """Get configured logger instance."""
    return logging.getLogger(name)
