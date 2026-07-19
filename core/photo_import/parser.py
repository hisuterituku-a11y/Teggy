from abc import ABC, abstractmethod
from typing import List
from core.photo_import.models import PhotoInfo, SourceType


class BaseParser(ABC):
    """Абстрактный парсер для всех источников."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self._is_cancelled = False

    @abstractmethod
    def parse(self, url: str) -> List[PhotoInfo]:
        """
        Парсит фотографии из источника.

        Args:
            url: Ссылка на страницу

        Returns:
            List[PhotoInfo]: Список найденных фотографий

        Raises:
            ParserError: Если не удалось распарсить
        """
        pass

    def cancel(self) -> None:
        """Отменяет парсинг."""
        self._is_cancelled = True

    def close(self) -> None:
        """Закрывает ресурсы."""
        pass