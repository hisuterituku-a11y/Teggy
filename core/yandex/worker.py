from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.yandex.yandex_router import YandexRouter


class YandexWorker(QThread):

    log = Signal(str)
    progress = Signal(str)
    finished = Signal(bool)

    def __init__(
        self,
        url: str,
        save_dir: Path,
        on_log=None,
        on_progress=None,
        on_finished=None,
        skip_existing=True
    ):
        super().__init__()

        self.url = url
        self.save_dir = Path(save_dir)

        self.skip_existing = skip_existing
        
        self._cancel = False

        if on_log:
            self.log.connect(on_log)

        if on_progress:
            self.progress.connect(on_progress)

        if on_finished:
            self.finished.connect(on_finished)

    # ===========================================
    # RUN
    # ===========================================

    def run(self):

        try:

            router = YandexRouter()

            # переопределяем вывод логов
            router.log = self._log

            router.run(
                self.url,
                save_dir=self.save_dir
            )

            self.finished.emit(True)

        except Exception as e:

            self._log(f"Ошибка: {e}")

            self.finished.emit(False)

    # ===========================================
    # LOG
    # ===========================================

    def _log(self, text):

        self.log.emit(text)

    # ===========================================
    # CANCEL
    # ===========================================

    def cancel(self):

        self._cancel = True