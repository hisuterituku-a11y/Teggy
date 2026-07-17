"""
Кастомные исключения для Tegi.
"""


class TegiError(Exception):
    """Базовое исключение для всех ошибок Tegi."""
    pass


class MetadataError(TegiError):
    """Ошибка при работе с метаданными."""
    pass


class CleanerError(TegiError):
    """Ошибка при очистке EXIF."""
    pass


class ConversionError(TegiError):
    """Ошибка при конвертации файлов."""
    pass


class TemplateError(TegiError):
    """Ошибка при работе с шаблонами."""
    pass


class ConfigError(TegiError):
    """Ошибка при работе с конфигурацией."""
    pass


class HistoryError(TegiError):
    """Ошибка при работе с историей."""
    pass