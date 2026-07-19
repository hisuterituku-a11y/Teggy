"""
Скачивание фотографий с поддержкой прогресса и отмены.
"""

from pathlib import Path
from typing import List, Optional, Callable
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

from core.photo_import.models import PhotoInfo, ImportStatus
from core.photo_import.exceptions import DownloadError, CancelledError


class Downloader:
    """
    Скачивает фотографии.

    Особенности:
    - многопоточность (max_workers)
    - повторные попытки (retries)
    - отмена
    - прогресс через callback
    - пропуск существующих файлов
    """

    def __init__(self, max_workers: int = 5, retries: int = 3):
        self.max_workers = max_workers
        self.retries = retries
        self._is_cancelled = False

    def _download_single(
        self,
        photo: PhotoInfo,
        save_dir: Path,
        skip_existing: bool
    ) -> PhotoInfo:
        """Скачивает один файл с повторными попытками."""
        if self._is_cancelled:
            photo.status = ImportStatus.CANCELLED
            photo.error = "Отменено"
            return photo

        # Определяем имя файла
        filename = photo.filename or photo.url.split('/')[-1].split('?')[0] or "unknown.jpg"
        save_path = save_dir / filename

        # Пропускаем, если уже есть
        if skip_existing and save_path.exists():
            photo.status = ImportStatus.SKIPPED
            photo.local_path = save_path
            photo.size = save_path.stat().st_size
            return photo

        # Скачиваем с повторами
        for attempt in range(self.retries):
            if self._is_cancelled:
                photo.status = ImportStatus.CANCELLED
                photo.error = "Отменено"
                return photo

            try:
                response = requests.get(
                    photo.url,
                    timeout=30,
                    stream=True,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                response.raise_for_status()

                # Сохраняем
                save_dir.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self._is_cancelled:
                            save_path.unlink(missing_ok=True)
                            photo.status = ImportStatus.CANCELLED
                            photo.error = "Отменено"
                            return photo
                        if chunk:
                            f.write(chunk)

                photo.status = ImportStatus.SUCCESS
                photo.local_path = save_path
                photo.size = save_path.stat().st_size
                return photo

            except requests.exceptions.RequestException as e:
                if attempt == self.retries - 1:
                    photo.status = ImportStatus.FAILED
                    photo.error = f"Ошибка: {e}"
                    return photo
                time.sleep(2 ** attempt)  # 1, 2, 4 секунды

        photo.status = ImportStatus.FAILED
        photo.error = "Не удалось скачать"
        return photo

    def download(
        self,
        photos: List[PhotoInfo],
        save_dir: Path,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        skip_existing: bool = True,
    ) -> List[PhotoInfo]:
        """
        Скачивает фотографии.

        Args:
            photos: Список PhotoInfo с URL
            save_dir: Папка для сохранения
            on_progress: Callback(скачано, всего, имя_файла)
            skip_existing: Пропускать существующие файлы

        Returns:
            List[PhotoInfo]: Обновлённый список с результатами
        """
        self._is_cancelled = False
        total = len(photos)
        completed = 0

        save_dir.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._download_single,
                    photo,
                    save_dir,
                    skip_existing
                ): photo for photo in photos
            }

            for future in as_completed(futures):
                if self._is_cancelled:
                    for f in futures:
                        f.cancel()
                    break

                result = future.result()
                completed += 1

                if on_progress:
                    filename = result.local_path.name if result.local_path else result.url
                    on_progress(completed, total, filename)

        # Возвращаем результаты
        return [future.result() for future in futures if not future.cancelled()]

    def cancel(self) -> None:
        """Отменяет скачивание."""
        self._is_cancelled = True