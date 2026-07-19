"""
Скачивание фотографий с поддержкой многопоточности и кэша.
"""

from pathlib import Path
from typing import List, Optional, Callable
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from datetime import datetime
import time

from core.photo_import.models import PhotoInfo, ImportStatus
from core.photo_import.exceptions import DownloadError, NetworkError, CancelledError


class Downloader:
    """
    Скачивает фотографии по URL.

    Особенности:
    - многопоточность (max_workers)
    - повторные попытки (retries)
    - кэш (пропуск уже скачанных)
    - отмена
    - прогресс через callback
    """

    def __init__(self, max_workers: int = 5, retries: int = 3):
        self.max_workers = max_workers
        self.retries = retries
        self._is_cancelled = False
        self._cache: dict = {}
        self._cache_file = Path.home() / ".teggy" / "import_cache.json"
        self._load_cache()

    def _load_cache(self) -> None:
        """Загружает кэш из файла."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except:
                self._cache = {}

    def _save_cache(self) -> None:
        """Сохраняет кэш в файл."""
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._cache_file, 'w', encoding='utf-8') as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def _is_cached(self, url: str) -> bool:
        """Проверяет, скачан ли файл по URL."""
        return url in self._cache

    def _add_to_cache(self, url: str, filename: str, file_hash: str = "") -> None:
        """Добавляет файл в кэш."""
        self._cache[url] = {
            "filename": filename,
            "hash": file_hash,
            "downloaded_at": datetime.now().isoformat()
        }
        self._save_cache()

    def _get_filename_from_url(self, url: str) -> str:
        """Извлекает имя файла из URL."""
        return url.split('/')[-1].split('?')[0] or "unknown.jpg"

    def _download_single(
        self,
        photo: PhotoInfo,
        save_dir: Path,
        skip_existing: bool
    ) -> PhotoInfo:
        """
        Скачивает один файл с повторными попытками.

        Returns:
            PhotoInfo с обновлённым статусом
        """
        if self._is_cancelled:
            photo.status = ImportStatus.CANCELLED
            photo.error = "Отменено пользователем"
            return photo

        # Проверяем кэш
        if skip_existing and self._is_cached(photo.url):
            photo.status = ImportStatus.SKIPPED
            photo.local_path = save_dir / self._cache[photo.url]["filename"]
            return photo

        # Определяем имя файла
        filename = photo.filename or self._get_filename_from_url(photo.url)
        save_path = save_dir / filename

        # Если файл уже существует физически
        if skip_existing and save_path.exists():
            photo.status = ImportStatus.SKIPPED
            photo.local_path = save_path
            self._add_to_cache(photo.url, filename)
            return photo

        # Скачиваем с повторами
        for attempt in range(self.retries):
            try:
                response = requests.get(
                    photo.url,
                    timeout=30,
                    stream=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                response.raise_for_status()

                # Проверяем, что это изображение
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    raise DownloadError(f"Не изображение: {content_type}")

                # Сохраняем
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self._is_cancelled:
                            save_path.unlink(missing_ok=True)
                            photo.status = ImportStatus.CANCELLED
                            photo.error = "Отменено пользователем"
                            return photo
                        if chunk:
                            f.write(chunk)

                # Вычисляем хеш
                file_hash = hashlib.md5(save_path.read_bytes()).hexdigest()

                photo.status = ImportStatus.SUCCESS
                photo.local_path = save_path
                photo.size = save_path.stat().st_size
                self._add_to_cache(photo.url, filename, file_hash)
                return photo

            except requests.exceptions.RequestException as e:
                if attempt == self.retries - 1:
                    photo.status = ImportStatus.FAILED
                    photo.error = f"Ошибка скачивания: {e}"
                    return photo
                time.sleep(2 ** attempt)  # exponential backoff

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
        Скачивает фотографии многопоточно.

        Args:
            photos: Список PhotoInfo с url
            save_dir: Папка для сохранения
            on_progress: Callback(скачано, всего, имя_файла)
            skip_existing: Пропускать существующие

        Returns:
            List[PhotoInfo]: Обновлённый список с результатами
        """
        self._is_cancelled = False
        total = len(photos)
        downloaded = 0

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
                    # Отменяем оставшиеся задачи
                    for f in futures:
                        f.cancel()
                    break

                result = future.result()
                downloaded += 1

                if on_progress:
                    current_file = result.local_path.name if result.local_path else result.url
                    on_progress(downloaded, total, current_file)

        return [future.result() for future in futures if not future.cancelled()]