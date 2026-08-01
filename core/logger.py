from __future__ import annotations

import logging
import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path


APP_DIR = Path.home() / ".teggy"
LOG_DIR = APP_DIR / "logs"
LOG_FILE = LOG_DIR / "teggy.log"
ERROR_LOG_FILE = LOG_DIR / "teggy-errors.log"
LEGACY_LOG_FILE = APP_DIR / "teggy.log"

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _same_file_handler(handler: logging.Handler, path: Path) -> bool:
    filename = getattr(handler, "baseFilename", None)
    if not filename:
        return False

    try:
        return Path(filename).resolve() == path.resolve()
    except OSError:
        return str(filename) == str(path)


def _migrate_legacy_log() -> None:
    """Сохраняет старый журнал после перехода в каталог ``logs``."""
    if not LEGACY_LOG_FILE.is_file() or LOG_FILE.exists():
        return

    try:
        shutil.copy2(LEGACY_LOG_FILE, LOG_FILE)
    except OSError:
        # Ошибка миграции не должна мешать запуску приложения.
        pass


def setup_logging() -> Path:
    """Настраивает общий журнал и отдельный журнал ошибок."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_log()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        _LOG_FORMAT,
        datefmt=_DATE_FORMAT,
    )

    if not any(_same_file_handler(handler, LOG_FILE) for handler in root_logger.handlers):
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if not any(
        _same_file_handler(handler, ERROR_LOG_FILE)
        for handler in root_logger.handlers
    ):
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=2 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    if not any(
        type(handler) is logging.StreamHandler
        for handler in root_logger.handlers
    ):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return LOG_FILE
