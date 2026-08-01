from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path.home() / ".teggy" / "logs"
LOG_FILE = LOG_DIR / "teggy.log"
ERROR_LOG_FILE = LOG_DIR / "teggy-errors.log"

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _has_file_handler(logger: logging.Logger, path: Path) -> bool:
    expected = str(path.resolve())
    return any(
        isinstance(handler, RotatingFileHandler)
        and str(Path(handler.baseFilename).resolve()) == expected
        for handler in logger.handlers
    )


def setup_logging() -> Path:
    """Настраивает журналы Teggy один раз и возвращает основной путь."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    if not _has_file_handler(root_logger, LOG_FILE):
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if not _has_file_handler(root_logger, ERROR_LOG_FILE):
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    if not any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in root_logger.handlers
    ):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    logging.captureWarnings(True)
    return LOG_FILE
