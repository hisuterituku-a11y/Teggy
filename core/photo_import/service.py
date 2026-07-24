"""
Главный фасад импорта фотографий.

GUI работает только через этот класс.
"""

from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
import uuid

from PySide6.QtCore import QThread

from core.photo_import.models import (
    ImportTask,
    ImportProgress,
    SourceType,
    ImportStatus,
)

from core.photo_import.providers import (
    YandexParser,
    GoogleParser,
    TwoGISParser,
)

from core.photo_import.downloader import Downloader

from core.photo_import.exceptions import (
    SourceNotSupportedError,
)

from core.photo_import.worker import ImportWorker


class PhotoImportService:
    """
    Главный сервис импорта.

    GUI ничего не знает о Parser, Downloader и потоках.
    """

    PARSERS = [
        YandexParser,
        GoogleParser,
        TwoGISParser,
    ]

    def __init__(
        self,
        headless: bool = True
    ):

        self.headless = headless
        self._current_task: Optional[ImportTask] = None

        self._thread: Optional[QThread] = None
        self._worker: Optional[ImportWorker] = None

        # Один downloader на всё время жизни сервиса.
        self._downloader = Downloader(
            max_workers=5,
            retries=3,
        )

    # =====================================================
    # Parser
    # =====================================================

    def _get_parser(
        self,
        url: str,
        source_type: SourceType,
    ):

        if source_type == SourceType.AUTO:

            for parser_cls in self.PARSERS:

                parser = parser_cls(
                    headless=self.headless
                )

                if parser.supports_url(url):
                    return parser

            raise SourceNotSupportedError(
                f"Не удалось определить источник: {url}"
            )

        mapping = {
            SourceType.YANDEX: YandexParser,
            SourceType.GOOGLE: GoogleParser,
            SourceType.TWOGIS: TwoGISParser,
        }

        parser_cls = mapping.get(source_type)

        if parser_cls is None:
            raise SourceNotSupportedError(
                f"Источник не поддерживается: {source_type}"
            )

        return parser_cls(
            headless=self.headless
        )

    # =====================================================
    # Default callbacks
    # =====================================================

    @staticmethod
    def _default_log(message: str):
        print(message)

    @staticmethod
    def _default_progress(progress: ImportProgress):
        pass

    # =====================================================
    # Start
    # =====================================================

    def start_import(
        self,
        url: str,
        save_dir: Path,
        source_type: SourceType = SourceType.AUTO,
        rename_files: bool = True,
        skip_existing: bool = True,
        on_progress: Optional[
            Callable[[ImportProgress], None]
        ] = None,
        on_log: Optional[
            Callable[[str], None]
        ] = None,
    ) -> str:

        if self._thread and self._thread.isRunning():
            raise RuntimeError(
                "Импорт уже выполняется."
            )

        task_id = (
            f"import_"
            f"{uuid.uuid4().hex[:8]}_"
            f"{datetime.now():%Y%m%d_%H%M%S}"
        )

        task = ImportTask(
            id=task_id,
            source_url=url,
            source_type=source_type,
            save_dir=save_dir,
            status=ImportStatus.PENDING,
        )

        self._current_task = task

        callbacks = {
            "on_progress": on_progress or self._default_progress,
            "on_log": on_log or self._default_log,
            "skip_existing": skip_existing,
            "rename_files": rename_files,
        }

        parser = self._get_parser(
            url,
            source_type,
        )

        self._thread = QThread()

        self._worker = ImportWorker(
            task=task,
            callbacks=callbacks,
            parser=parser,
            downloader=self._downloader,
        )

        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)

        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)

        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

        return task_id

    # =====================================================
    # Stop
    # =====================================================

    def stop_import(self):

        if self._worker:
            self._worker.cancel()

    # =====================================================
    # Status
    # =====================================================

    def get_status(
        self,
        task_id: str,
    ) -> Optional[ImportTask]:

        if (
            self._current_task
            and self._current_task.id == task_id
        ):
            return self._current_task

        return None

    # =====================================================
    # Cleanup
    # =====================================================

    def _cleanup_thread(self):

        if self._current_task:
            self._current_task.finished_at = datetime.now()

        if self._thread:
            self._thread.deleteLater()

        self._thread = None
        self._worker = None
            # =====================================================
    # CANCEL ALIAS
    # =====================================================

    def cancel(self, task_id: str = None):
        """
        Совместимость с GUI.

        GUI вызывает cancel(),
        внутри используем stop_import().
        """

        self.stop_import()