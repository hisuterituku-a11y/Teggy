from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.statistics import StatisticsStore
from core.yandex.worker import YandexWorker


FinishedCallback = Callable[[bool], None]
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def _image_files(folder: Path) -> set[Path]:
    if not folder.exists():
        return set()
    return {
        path.resolve()
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES
    }


class YandexService:
    """Управляет единственным активным импортом из Яндекс Карт."""

    def __init__(self) -> None:
        self.worker: YandexWorker | None = None

    def start(
        self,
        url: str,
        save_dir: Path,
        download_organization_photos: bool = True,
        download_review_photos: bool = True,
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

        existing_images = _image_files(save_dir)

        worker = YandexWorker(
            url=url,
            save_dir=save_dir,
            download_organization_photos=download_organization_photos,
            download_review_photos=download_review_photos,
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

            if success:
                downloaded = len(_image_files(save_dir) - existing_images)
                if downloaded:
                    StatisticsStore().increment(downloaded=downloaded)

            if on_finished is not None:
                on_finished(success)

        worker.finished.connect(handle_finished)
        worker.start()
        return worker

    def cancel(self) -> None:
        worker = self.worker
        if worker is not None and worker.isRunning():
            worker.cancel()
