from pathlib import Path
from unittest.mock import Mock

from core.photo_import.worker import ImportWorker
from core.photo_import.models import (
    ImportTask,
    SourceType,
    ImportStatus
)


def test_worker_success(tmp_path):

    task = ImportTask(
        id="test1",
        source_url="https://yandex.ru/maps/test",
        source_type=SourceType.YANDEX,
        save_dir=tmp_path
    )


    parser = Mock()

    downloader = Mock()


    from core.photo_import.models import PhotoInfo


    photos = [
        PhotoInfo(
            url="http://test/photo.jpg",
            filename="photo.jpg",
            source=SourceType.YANDEX
        )
    ]


    parser.parse.return_value = photos


    result_photo = photos[0]
    result_photo.status = ImportStatus.SUCCESS


    downloader.download.return_value = [
        result_photo
    ]


    logs = []
    progresses = []


    callbacks = {
        "on_progress": progresses.append,
        "on_log": logs.append,
        "skip_existing": True
    }


    worker = ImportWorker(
        task,
        callbacks,
        parser,
        downloader
    )


    worker.run()


    assert task.status == ImportStatus.SUCCESS

    assert task.downloaded == 1

    assert len(logs) > 0

    assert len(progresses) > 0



def test_worker_no_photos(tmp_path):

    task = ImportTask(
        id="test2",
        source_url="https://yandex.ru/maps/test",
        source_type=SourceType.YANDEX,
        save_dir=tmp_path
    )


    parser = Mock()
    downloader = Mock()


    parser.parse.return_value = []


    worker = ImportWorker(
        task,
        {
            "on_progress": lambda x: None,
            "on_log": lambda x: None
        },
        parser,
        downloader
    )


    worker.run()


    assert task.status == ImportStatus.FAILED