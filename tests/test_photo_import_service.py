from unittest.mock import Mock

from PySide6.QtCore import (
    QCoreApplication,
    QEventLoop,
    QTimer,
)

from core.photo_import.service import PhotoImportService
from core.photo_import.models import (
    SourceType,
    ImportStatus,
    PhotoInfo,
)



def test_service_start_import(tmp_path):

    app = (
        QCoreApplication.instance()
        or QCoreApplication([])
    )


    service = PhotoImportService()


    logs = []
    progress = []



    fake_photo = PhotoInfo(
        url="http://test/photo.jpg",
        filename="photo.jpg",
        source=SourceType.YANDEX
    )



    # -------------------------
    # fake parser
    # -------------------------

    fake_parser = Mock()

    fake_parser.parse.return_value = [
        fake_photo
    ]

    fake_parser.close = Mock()



    # -------------------------
    # fake downloader
    # -------------------------

    fake_downloader = Mock()

    fake_photo.status = ImportStatus.SUCCESS


    fake_downloader.download.return_value = [
        fake_photo
    ]



    # ВАЖНО:
    # заменяем уже созданный объект

    service._downloader = fake_downloader



    # -------------------------
    # worker finish wait
    # -------------------------

    loop = QEventLoop()



    task_id = service.start_import(

        url="https://yandex.ru/maps/test",

        save_dir=tmp_path,

        source_type=SourceType.YANDEX,

        on_progress=progress.append,

        on_log=logs.append

    )


    # подменяем parser уже после создания worker
    service._worker.parser = fake_parser



    service._worker.finished.connect(
        loop.quit
    )


    QTimer.singleShot(
        5000,
        loop.quit
    )


    loop.exec()



    task = service.get_status(task_id)



    assert task is not None

    assert task.status == ImportStatus.SUCCESS

    assert task.downloaded == 1

    assert len(logs) > 0

    assert len(progress) > 0