from pathlib import Path

from core.yandex.worker import YandexWorker


class YandexService:

    def __init__(self):

        self.worker = None

    def start(
        self,
        url: str,
        save_dir: Path,
        download_stories: bool = False,
        on_log=None,
        on_progress=None,
        on_finished=None,
        skip_existing=True
    ):

        self.worker = YandexWorker(
            url=url,
            save_dir=save_dir,
            download_stories=download_stories,
            on_log=on_log,
            on_progress=on_progress,
            on_finished=on_finished,
            skip_existing=skip_existing
        )

        self.worker.start()

        return self.worker

    def cancel(self):

        if self.worker:
            self.worker.cancel()