from PySide6.QtCore import QThread, Signal
from pathlib import Path
from core.worker import ProcessingWorker
from core.exceptions import TegiError


class ProcessingThread(QThread):
    """Поток для обработки файлов без зависания интерфейса."""

    progress = Signal(int, int)  # current, total
    log = Signal(str)
    finished = Signal(dict)  # статистика
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = ProcessingWorker()
        self._is_cancelled = False
        self.folder_path = ""
        self.file_list = None
        self.output_dir = None
        self.metadata = {}
        self.tags = []
        self.delete_original = False
        self.quality = 95

    def setup(
        self,
        folder_path: str,
        file_list: list = None,
        metadata: dict = None,
        tags: list = None,
        delete_original: bool = False,
        quality: int = 95,
        output_dir: str = None
    ):
        """Настраивает параметры обработки."""
        self.folder_path = folder_path
        self.file_list = file_list
        self.metadata = metadata or {}
        self.tags = tags or []
        self.delete_original = delete_original
        self.quality = quality
        self.output_dir = output_dir

    def cancel(self):
        """Отменяет обработку."""
        self._is_cancelled = True

    def run(self):
        """Запускает обработку в отдельном потоке."""
        try:
            self.worker.set_metadata(**self.metadata)
            self.worker.set_tags(self.tags)
            self.worker.set_processing_options(
                delete_original=self.delete_original,
                quality=self.quality
            )

            self.worker.set_callbacks(
                on_progress=self._on_progress,
                on_log=self._on_log
            )

            # Если передан список файлов — используем его
            if self.file_list:
                stats = self.worker.process_file_list(
                    self.file_list,
                    output_dir=self.output_dir or str(Path(self.folder_path) / "Teggy")
                )
            else:
                stats = self.worker.process_folder(
                    self.folder_path,
                    output_dir=self.output_dir
                )

            if self._is_cancelled:
                self.log.emit("⏹️ Обработка отменена")
                self.finished.emit({"cancelled": True})
            else:
                self.finished.emit(stats)

        except TegiError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Критическая ошибка: {e}")

    def _on_progress(self, current: int, total: int):
        """Колбэк прогресса."""
        self.progress.emit(current, total)

    def _on_log(self, message: str):
        """Колбэк лога."""
        self.log.emit(message)