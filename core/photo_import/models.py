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


# ===== ИСКЛЮЧЕНИЯ =====

class PhotoImportError(Exception):
    """Базовое исключение."""
    pass


class ParserError(PhotoImportError):
    """Ошибка парсинга."""
    pass


class DownloadError(PhotoImportError):
    """Ошибка скачивания."""
    pass


class NetworkError(PhotoImportError):
    """Ошибка сети."""
    pass


class CancelledError(PhotoImportError):
    """Отмена пользователем."""
    pass


class SourceNotSupportedError(PhotoImportError):
    """Неподдерживаемый источник."""
    pass