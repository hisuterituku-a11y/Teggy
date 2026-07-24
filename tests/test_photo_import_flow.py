from unittest.mock import Mock

from core.photo_import.models import (
    ImportTask,
    SourceType,
    ImportStatus,
    PhotoInfo,
)

from core.photo_import.worker import ImportWorker



def test_full_import_flow(tmp_path):

    task = ImportTask(
        id="flow_test",
        source_url="https://yandex.ru/maps/test",
        source_type=SourceType.YANDEX,
        save_dir=tmp_path
    )


    photo = PhotoInfo(
        url="http://test/photo.jpg",
        filename="clinic.jpg",
        source=SourceType.YANDEX,
        category="interior",
        is_review=False
    )


    parser = Mock()

    parser.parse.return_value = [
        photo
    ]

    parser.close = Mock()



    photo.status = ImportStatus.SUCCESS


    downloader = Mock()

    downloader.download.return_value = [
        photo
    ]



    logs = []
    progress = []



    worker = ImportWorker(
        task,
        {
            "skip_existing": True,
            "on_log": logs.append,
            "on_progress": progress.append,
        },
        parser,
        downloader
    )



    worker.run()



    assert task.status == ImportStatus.SUCCESS

    assert task.downloaded == 1

    assert task.photos[0].category == "interior"

    assert task.photos[0].status == ImportStatus.SUCCESS

    assert len(logs) > 0