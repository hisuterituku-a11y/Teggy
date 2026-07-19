"""
Главный фасад для импорта фотографий.

GUI работает только с этим классом.
"""
from threading import Event
from pathlib import Path
from typing import Optional, Callable, List
import uuid
from PySide6.QtCore import QThread, QObject
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
        self._thread: Optional[QThread] = None
        self._worker: Optional[ImportWorker] = None
        self._downloader = Downloader(max_workers=5, retries=3)
        self._on_progress: Optional[Callable] = None
        self._on_log: Optional[Callable] = None
        self._stop_event = False

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
        if self._stop_event:
            raise CancelledError("Импорт отменён пользователем")

    def _run_import(self, task: ImportTask, callbacks: dict) -> None:
        """Запускает импорт в отдельном потоке."""
        self._on_progress = callbacks.get('on_progress')
        self._on_log = callbacks.get('on_log')

        try:
            self._log(f"Начинаем импорт: {task.source_url}")
            task.status = ImportStatus.PARSING
            self._notify_progress(task, "Парсинг страницы...")

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

            def on_download_progress(downloaded, total, filename):
                task.downloaded = downloaded
                self._notify_progress(task, f"Скачано {downloaded}/{total}", filename)

            results = self._downloader.download(
                photos=photos,
                save_dir=task.save_dir,
                on_progress=on_download_progress,
                skip_existing=callbacks.get('skip_existing', True)
            )

            task.photos = results
            task.downloaded = sum(1 for p in results if p.status == ImportStatus.SUCCESS)
            task.failed = sum(1 for p in results if p.status == ImportStatus.FAILED)
            task.skipped = sum(1 for p in results if p.status == ImportStatus.SKIP)

            if self._stop_event:
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
        rename_files: bool = True,
        skip_existing: bool = True,
        on_progress: Optional[Callable[[ImportProgress], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> str:
        if self._thread and self._thread.isRunning():
            raise RuntimeError("Импорт уже запущен")

        self._stop_event = False

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
            'rename_files': rename_files,
        }

        from PySide6.QtCore import QThread
        from core.photo_import.worker import ImportWorker

        self._thread = QThread()
        self._worker = ImportWorker(task, callbacks)
        self._worker.moveToThread(self._thread)

        self._worker.progress.connect(on_progress or self._default_progress)
        self._worker.log.connect(on_log or self._default_log)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)

        # Очистка после завершения потока
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.started.connect(self._worker.run)
        self._thread.start()

        return task_id

    def stop_import(self) -> None:
        """Останавливает текущий импорт."""
        self._stop_event = True
        if self._downloader:
            self._downloader.cancel()

    def get_status(self, task_id: str) -> Optional[ImportTask]:
        """Возвращает статус задачи."""
        if self._current_task and self._current_task.id == task_id:
            return self._current_task
        return None

    def _on_worker_finished(self):
        """Обработчик завершения работы воркера."""
        if self._thread and self._thread.isRunning():
            # Не вызываем wait() здесь — это приведёт к deadlock
            self._thread.quit()
            # После quit поток завершится сам, и вызовется thread.finished
            # Подключаем очистку к thread.finished
            if not hasattr(self, '_thread_cleanup_connected'):
                self._thread.finished.connect(self._cleanup_thread)
                self._thread_cleanup_connected = True

    def _on_worker_error(self, error_message: str):
        """Обработчик ошибки в воркере."""
        print(f"Worker error: {error_message}")
        self._on_worker_finished()

    def _cleanup_thread(self):
        """Очистка после завершения потока."""
        if self._thread:
            self._thread.deleteLater()
            self._thread = None
        self._worker = None
        self._thread_cleanup_connected = False