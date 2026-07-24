from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class SourceType(Enum):
    """Тип источника фотографий."""
    AUTO = "auto"
    YANDEX = "yandex"
    GOOGLE = "google"
    TWOGIS = "2gis"


class ImportStatus(Enum):
    """Статус импорта."""
    PENDING = "pending"
    PARSING = "parsing"
    DOWNLOADING = "downloading"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIP = "skip"


@dataclass
class PhotoInfo:
    """Информация об одной фотографии."""

    url: str
    filename: str
    source: SourceType

    # новая информация
    category: str = ""
    is_review: bool = False

    status: ImportStatus = ImportStatus.PENDING
    local_path: Optional[Path] = None
    size: Optional[int] = None
    error: Optional[str] = None


@dataclass
class ImportTask:
    """Задача на импорт."""
    id: str
    source_url: str
    source_type: SourceType
    save_dir: Path
    photos: List[PhotoInfo] = field(default_factory=list)
    total: int = 0
    downloaded: int = 0
    failed: int = 0
    skipped: int = 0
    status: ImportStatus = ImportStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None


@dataclass
class ImportProgress:
    """Прогресс для GUI."""
    task_id: str
    total: int
    downloaded: int
    failed: int
    skipped: int
    current_file: str
    percent: float
    status: ImportStatus
    message: str = ""


# ИСПРАВЛЕНО: раньше здесь дублировались классы исключений
# (PhotoImportError, ParserError, DownloadError, NetworkError,
# CancelledError, SourceNotSupportedError) — те же самые по имени, но
# СОВСЕМ ДРУГИЕ по идентичности классы, чем в core/photo_import/exceptions.py.
#
# Это опасный баг: providers.py (и, вероятно, другой код) ловит
# исключения через `from core.photo_import.exceptions import ParserError`.
# Если где-то в проекте исключение поднимается через
# `from core.photo_import.models import ParserError`, то `except ParserError`
# в providers.py его НЕ поймает, несмотря на одинаковое имя класса —
# для Python это два независимых класса. Ошибка тихо "утечёт" мимо
# обработчика вместо того, чтобы быть аккуратно обработанной.
#
# Исключения теперь определены только в одном месте — в
# core/photo_import/exceptions.py. Если models.py где-то нужно
# использовать эти классы (например, для аннотаций типов), их следует
# импортировать оттуда:
#
#     from core.photo_import.exceptions import (
#         PhotoImportError,
#         ParserError,
#         DownloadError,
#         NetworkError,
#         CancelledError,
#         SourceNotSupportedError,
#     )
#
# а не переопределять заново.