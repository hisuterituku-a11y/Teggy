"""
Главный фасад для импорта фотографий.

GUI работает только с этим классом.
"""

from pathlib import Path
from typing import Optional, Callable, List
import uuid
from threading import Thread, Event
from datetime import datetime

from core.photo_import.models import (
    ImportTask, ImportProgress, PhotoInfo,
    SourceType, ImportStatus
)
from core.photo_import.providers import YandexParser, GoogleParser, TwoGISParser
from core.photo_import.downloader import Downloader
from core.photo_import.exceptions import (
    SourceNotSupportedError, CancelledError, ParserError
)


class PhotoImportService:
    """
    Сервис импорта фотографий.

    Точка входа для GUI.
    """

    PARSERS = [YandexParser, GoogleParser, TwoGISParser]

    def __init__(self):
        self._current_task: Optional[ImportTask] = None
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._downloader = Downloader(max_workers=5, retries=3)
        self._on_progress: Optional[Callable] = None
        self._on_log: Optional[Callable] = None

    def _get_parser(self, url: str, source_type: SourceType):
        """Возвращает парсер для указанного источника или автоопределяет."""
        if source_type == SourceType.AUTO:
            for ParserClass in self.PARSERS:
                parser = ParserClass()
                if parser.supports_url(url):
                    return parser
            raise SourceNotSupportedError(f"Не удалось определить источник: {url}")

        parsers = {
            SourceType.YANDEX: YandexParser,
            SourceType.GOOGLE: GoogleParser,
            SourceType.TWOGIS: TwoGISParser,
        }
        parser_cls = parsers.get(source_type)
        if not parser_cls:
            raise SourceNotSupportedError(f"Источник не поддерживается: {source_type}")
        return parser_cls()

    def _log(self, message: str) -> None:
        """Отправляет сообщение в лог."""
        if self._on_log:
            self._on_log(message)

    def _notify_progress(self, task: ImportTask, message: str = "", current_file: str = "") -> None:
        """Отправляет прогресс в GUI."""
        if not self._on_progress:
            return

        percent = 0
        if task.total > 0:
            percent = ((task.downloaded + task.failed + task.skipped) / task.total) * 100

        progress = ImportProgress(
            task_id=task.id,
            total=task.total,
            downloaded=task.downloaded,
            failed=task.failed,
            skipped=task.skipped,
            current_file=current_file,
            percent=min(percent, 100),
            status=task.status,
            message=message
        )
        self._on_progress(progress)

    def _check_cancelled(self) -> None:
        """Проверяет, не отменён ли импорт."""
        if self._stop_event.is_set():
            raise CancelledError("Импорт отменён пользователем")

    def _run_import(self, task: ImportTask, callbacks: dict) -> None:
        """Запускает импорт в отдельном потоке."""
        self._on_progress = callbacks.get('on_progress')
        self._on_log = callbacks.get('on_log')

        try:
            self._log(f"Начинаем импорт: {task.source_url}")
            task.status = ImportStatus.PARSING
            self._notify_progress(task, "Парсинг страницы...")

            # 1. Парсим фотографии
            parser = self._get_parser(task.source_url, task.source_type)
            photos = parser.parse(task.source_url)
            parser.close()

            if not photos:
                self._log("Фотографии не найдены")
                task.status = ImportStatus.FAILED
                self._notify_progress(task, "Фотографии не найдены")
                return

            self._log(f"Найдено фотографий: {len(photos)}")
            task.photos = photos
            task.total = len(photos)
            task.status = ImportStatus.DOWNLOADING
            self._notify_progress(task, f"Скачивание {len(photos)} файлов...")

            # 2. Скачиваем фотографии
            def on_download_progress(downloaded: int, total: int, filename: str):
                task.downloaded = downloaded
                self._notify_progress(task, f"Скачано {downloaded}/{total}", filename)

            results = self._downloader.download(
                photos=photos,
                save_dir=task.save_dir,
                on_progress=on_download_progress,
                skip_existing=callbacks.get('skip_existing', True)
            )

            # 3. Обновляем статистику
            task.photos = results
            task.downloaded = sum(1 for p in results if p.status == ImportStatus.SUCCESS)
            task.failed = sum(1 for p in results if p.status == ImportStatus.FAILED)
            task.skipped = sum(1 for p in results if p.status == ImportStatus.SKIPPED)

            if self._stop_event.is_set():
                task.status = ImportStatus.CANCELLED
                self._log("Импорт отменён")
                self._notify_progress(task, "Импорт отменён")
                return

            task.status = ImportStatus.SUCCESS
            self._log(f"Импорт завершён: скачано {task.downloaded}, пропущено {task.skipped}, ошибок {task.failed}")
            self._notify_progress(task, "Импорт завершён")

        except CancelledError:
            task.status = ImportStatus.CANCELLED
            self._log("Импорт отменён пользователем")
            self._notify_progress(task, "Импорт отменён")
        except Exception as e:
            task.status = ImportStatus.FAILED
            self._log(f"Ошибка: {e}")
            self._notify_progress(task, f"Ошибка: {e}")
        finally:
            task.finished_at = datetime.now()

    def start_import(
        self,
        url: str,
        save_dir: Path,
        source_type: SourceType = SourceType.AUTO,
        max_photos: int = 100,
        rename_files: bool = True,
        skip_existing: bool = True,
        on_progress: Optional[Callable[[ImportProgress], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Запускает импорт фотографий.

        Returns:
            str: ID задачи
        """
        # Проверяем, не запущен ли уже импорт
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Импорт уже запущен")

        self._stop_event.clear()

        task_id = f"import_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = ImportTask(
            id=task_id,
            source_url=url,
            source_type=source_type,
            save_dir=save_dir,
            status=ImportStatus.PENDING
        )
        self._current_task = task

        callbacks = {
            'on_progress': on_progress,
            'on_log': on_log,
            'skip_existing': skip_existing,
            'max_photos': max_photos,
            'rename_files': rename_files,
        }

        self._thread = Thread(target=self._run_import, args=(task, callbacks), daemon=True)
        self._thread.start()

        return task_id

    def stop_import(self) -> None:
        """Останавливает текущий импорт."""
        self._stop_event.set()
        if self._downloader:
            self._downloader.cancel()

    def get_status(self, task_id: str) -> Optional[ImportTask]:
        """Возвращает статус задачи."""
        if self._current_task and self._current_task.id == task_id:
            return self._current_task
        return None