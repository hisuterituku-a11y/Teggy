from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.yandex.worker import YandexWorker


FinishedCallback = Callable[[bool], None]


class YandexService:
    """Управляет единственным активным импортом из Яндекс Карт."""

    def __init__(self) -> None:
        self.worker: YandexWorker | None = None

    def start(
        self,
        url: str,
        save_dir: Path,
        download_stories: bool = False,
        download_videos: bool = False,
        on_log=None,
        on_progress=None,
        on_finished: FinishedCallback | None = None,
        skip_existing: bool = True,
    ) -> YandexWorker:
        current_worker = self.worker
        if current_worker is not None and current_worker.isRunning():
            raise RuntimeError("Импорт из Яндекс Карт уже выполняется")

        worker = YandexWorker(
            url=url,
            save_dir=save_dir,
            download_stories=download_stories,
            download_videos=download_videos,
            on_log=on_log,
            on_progress=on_progress,
            skip_existing=skip_existing,
        )
        self.worker = worker

        def handle_finished(success: bool) -> None:
            if self.worker is worker:
                self.worker = None

            if on_finished is not None:
                on_finished(success)

        worker.finished.connect(handle_finished)
        worker.start()
        return worker

    def cancel(self) -> None:
        worker = self.worker
        if worker is not None and worker.isRunning():
            worker.cancel()
