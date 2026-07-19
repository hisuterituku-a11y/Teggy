from PySide6.QtCore import QObject, Signal
from core.photo_import.models import ImportProgress, ImportTask, ImportStatus
from core.photo_import.providers import YandexParser
from core.photo_import.downloader import Downloader
from core.photo_import.exceptions import CancelledError


class ImportWorker(QObject):
    progress = Signal(ImportProgress)
    log = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, task, callbacks=None):
        super().__init__()
        self.task = task
        self.callbacks = callbacks or {}
        self._is_cancelled = False
        self._downloader = Downloader()

    def run(self):
        """Запускает импорт в фоновом потоке."""
        try:
            self.log.emit(f"Начинаем импорт: {self.task.source_url}")
            self.task.status = ImportStatus.PARSING
            self._notify_progress("Парсинг страницы...")

            # 1. Парсим фотографии
            parser = YandexParser()
            photos = parser.parse(self.task.source_url)
            parser.close()

            if not photos:
                self.log.emit("Фотографии не найдены")
                self.task.status = ImportStatus.FAILED
                self._notify_progress("Фотографии не найдены")
                self.finished.emit()
                return

            self.log.emit(f"Найдено фотографий: {len(photos)}")
            self.task.photos = photos
            self.task.total = len(photos)
            self.task.status = ImportStatus.DOWNLOADING
            self._notify_progress(f"Скачивание {len(photos)} файлов...")

            # 2. Скачиваем фотографии
            def on_download_progress(downloaded, total, filename):
                self.task.downloaded = downloaded
                self._notify_progress(f"Скачано {downloaded}/{total}", filename)
                

            results = self._downloader.download(
                photos=photos,
                save_dir=self.task.save_dir,
                on_progress=on_download_progress,
                skip_existing=self.callbacks.get('skip_existing', True)
            )
          
            for p in results[:5]:
                print(f"{p.filename}: {p.status}")
            # 3. Обновляем статистику
            self.task.photos = results
            self.task.downloaded = sum(1 for p in results if p.status == ImportStatus.SUCCESS)
            self.task.failed = sum(1 for p in results if p.status == ImportStatus.FAILED)
            self.task.skipped = sum(1 for p in results if p.status == ImportStatus.SKIP)

            self.task.status = ImportStatus.SUCCESS
            self.log.emit(f"Импорт завершён: скачано {self.task.downloaded}, пропущено {self.task.skipped}, ошибок {self.task.failed}")
            self._notify_progress("Импорт завершён")
            self.finished.emit()

        except CancelledError:
            self.task.status = ImportStatus.CANCELLED
            self.log.emit("Импорт отменён")
            self.finished.emit()
        except Exception as e:
            self.task.status = ImportStatus.FAILED
            self.log.emit(f"Ошибка: {e}")
            self.error.emit(str(e))
            self.finished.emit()

    def _notify_progress(self, message: str, current_file: str = ""):
        percent = 0
        if self.task.total > 0:
            percent = ((self.task.downloaded + self.task.failed + self.task.skipped) / self.task.total) * 100

        progress = ImportProgress(
            task_id=self.task.id,
            total=self.task.total,
            downloaded=self.task.downloaded,
            failed=self.task.failed,
            skipped=self.task.skipped,
            current_file=current_file,
            percent=min(percent, 100),
            status=self.task.status,
            message=message
        )
        self.progress.emit(progress)

    def cancel(self):
        self._is_cancelled = True
        if self._downloader:
            self._downloader.cancel()