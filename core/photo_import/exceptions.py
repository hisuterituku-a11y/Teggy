"""
Исключения модуля импорта фотографий.

Иерархия:
    PhotoImportError (базовое)
        ├── ParserError        # Ошибка парсинга
        ├── DownloadError      # Ошибка скачивания
        ├── NetworkError       # Ошибка сети
        ├── CancelledError     # Отмена пользователем
        └── SourceNotSupportedError  # Неподдерживаемый источник
"""


class PhotoImportError(Exception):
    """Базовое исключение для всех ошибок импорта."""
    pass


class ParserError(PhotoImportError):
    """Ошибка при парсинге страницы источника."""
    pass


class DownloadError(PhotoImportError):
    """Ошибка при скачивании файла."""
    pass


class NetworkError(PhotoImportError):
    """Ошибка сети при запросе."""
    pass


class CancelledError(PhotoImportError):
    """Операция отменена пользователем."""
    pass


class SourceNotSupportedError(PhotoImportError):
    """Источник не поддерживается текущей реализацией."""
    pass