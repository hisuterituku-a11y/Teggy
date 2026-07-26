"""Фоновая проверка обновлений для интерфейса Teggy."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot

from core.update_checker import ReleaseInfo, UpdateCheckError, check_for_updates


class UpdateWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    @Slot()
    def run(self) -> None:
        try:
            release = check_for_updates()
        except UpdateCheckError as error:
            self.failed.emit(str(error))
        else:
            self.finished.emit(release)


class UpdateService(QObject):
    update_available = Signal(object)
    no_update = Signal()
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: UpdateWorker | None = None

    def check(self) -> bool:
        """Запускает проверку и возвращает False, если она уже выполняется."""
        if self._thread is not None and self._thread.isRunning():
            return False

        thread = QThread(self)
        worker = UpdateWorker()
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._handle_release)
        worker.failed.connect(self.failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(self._clear_thread)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker
        thread.start()
        return True

    @Slot(object)
    def _handle_release(self, release: ReleaseInfo) -> None:
        if release.is_update_available:
            self.update_available.emit(release)
        else:
            self.no_update.emit()

    @Slot()
    def _clear_thread(self) -> None:
        self._thread = None
        self._worker = None
