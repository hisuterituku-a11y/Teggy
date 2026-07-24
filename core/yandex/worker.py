from __future__ import annotations

from pathlib import Path

from core.yandex.diagnostics import (
    format_exception_report,
    save_diagnostic_report,
)

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
        skip_existing: bool = True,
    ):
        super().__init__()

        self.url = url
        self.save_dir = Path(save_dir)
        self.skip_existing = skip_existing

        self._cancel_requested = False
        self._router: YandexRouter | None = None

        if on_log:
            self.log.connect(on_log)

        if on_progress:
            self.progress.connect(on_progress)

        if on_finished:
            self.finished.connect(on_finished)

    def run(self) -> None:
        success = False

        try:
            router = YandexRouter()
            self._router = router

            router.log = self._log
            router.progress = self._progress

            if self._cancel_requested:
                router.cancel()

            success = router.run(
                self.url,
                save_dir=self.save_dir,
                skip_existing=self.skip_existing,
            )

        except Exception as exc:
            report = format_exception_report(
                stage="YandexWorker",
                exc=exc,
                url=self.url,
            )

            for line in report.splitlines():
                self._log(line)

            try:
                diagnostic_dir = save_diagnostic_report(
                    save_dir=self.save_dir,
                    stage="YandexWorker",
                    exc=exc,
                    url=self.url,
                    log_lines=report.splitlines(),
                )
                self._log(
                    f"[ERROR] Диагностика сохранена: {diagnostic_dir}"
                )
            except Exception as diagnostic_exc:
                self._log(
                    "[ERROR] Не удалось сохранить диагностику: "
                    f"{diagnostic_exc}"
                )

            success = False

        finally:
            self._router = None
            self.finished.emit(success)

    def _log(self, text: str) -> None:
        self.log.emit(str(text))

    def _progress(self, text: str) -> None:
        self.progress.emit(str(text))

    def cancel(self) -> None:
        self._cancel_requested = True

        self._log("Запрошена отмена операции...")

        router = self._router

        if router is not None:
            router.cancel()

        self.requestInterruption()
