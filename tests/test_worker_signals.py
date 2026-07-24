from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer
from unittest.mock import Mock

from core.photo_import.worker import ImportWorker
from core.photo_import.models import (
    ImportTask,
    SourceType,
    PhotoInfo,
    ImportStatus,
)



def test_worker_emits_signals(tmp_path):

    app = (
        QCoreApplication.instance()
        or QCoreApplication([])
    )


    task = ImportTask(
        id="signal_test",
        source_url="test",
        source_type=SourceType.YANDEX,
        save_dir=tmp_path
    )


    photo = PhotoInfo(
        url="test",
        filename="a.jpg",
        source=SourceType.YANDEX
    )


    parser = Mock()
    parser.parse.return_value = [photo]
    parser.close = Mock()


    photo.status = ImportStatus.SUCCESS


    downloader = Mock()
    downloader.download.return_value = [photo]


    worker = ImportWorker(
        task,
        {
            "skip_existing": True
        },
        parser,
        downloader
    )


    logs = []
    progresses = []
    finished = []


    worker.log.connect(
        logs.append
    )

    worker.progress.connect(
        progresses.append
    )

    worker.finished.connect(
        lambda: finished.append(True)
    )


    worker.run()


    assert len(logs) > 0

    assert len(progresses) > 0

    assert finished == [True]