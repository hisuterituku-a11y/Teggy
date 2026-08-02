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
        pass


def _create_session_handler(
    path: Path,
    *,
    max_bytes: int,
    backup_count: int,
    level: int,
    formatter: logging.Formatter,
) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=True,
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)

    # Каждый запуск получает чистый текущий журнал. Предыдущий запуск остаётся
    # в teggy.log.1, teggy.log.2 и так далее, поэтому история не теряется.
    if path.is_file() and path.stat().st_size > 0:
        handler.doRollover()

    return handler


def setup_logging() -> Path:
    """Настраивает текущий журнал сессии и отдельный журнал ошибок."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_log()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        _LOG_FORMAT,
        datefmt=_DATE_FORMAT,
    )

    if not any(_same_file_handler(handler, LOG_FILE) for handler in root_logger.handlers):
        root_logger.addHandler(
            _create_session_handler(
                LOG_FILE,
                max_bytes=5 * 1024 * 1024,
                backup_count=5,
                level=logging.INFO,
                formatter=formatter,
            )
        )

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
