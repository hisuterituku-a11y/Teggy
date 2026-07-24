import time
from unittest.mock import Mock, patch

from core.photo_import.downloader import Downloader
from core.photo_import.models import (
    PhotoInfo,
    SourceType,
    ImportStatus
)


def make_photo(i):
    return PhotoInfo(
        url=f"https://example.com/{i}.jpg",
        filename=f"{i}.jpg",
        source=SourceType.YANDEX,
    )


@patch("core.photo_import.downloader.requests.get")
def test_cancel_during_download(mock_get, tmp_path):

    response = Mock()
    response.content = b"12345"
    response.raise_for_status = Mock()

    def slow_request(*args, **kwargs):
        time.sleep(0.2)
        return response

    mock_get.side_effect = slow_request


    photos = [
        make_photo(i)
        for i in range(20)
    ]


    downloader = Downloader(
        max_workers=2,
        retries=1
    )


    results = []


    def progress(done, total, filename):

        results.append(done)

        if done == 2:
            downloader.cancel()


    output = downloader.download(
        photos,
        tmp_path,
        on_progress=progress
    )


    assert len(output) == 20


    cancelled = [
        p for p in output
        if p.status == ImportStatus.CANCELLED
    ]


    success = [
        p for p in output
        if p.status == ImportStatus.SUCCESS
    ]


    assert len(cancelled) > 0
    assert len(success) > 0