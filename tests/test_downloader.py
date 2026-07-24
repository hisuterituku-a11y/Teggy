from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.photo_import.downloader import Downloader
from core.photo_import.models import PhotoInfo, SourceType, ImportStatus


def make_photo(name="photo.jpg", url="https://example.com/test.jpg"):
    return PhotoInfo(
        url=url,
        filename=name,
        source=SourceType.YANDEX,
    )


# ---------------------------------------------------------
# SUCCESS
# ---------------------------------------------------------

@patch("core.photo_import.downloader.requests.get")
def test_download_success(mock_get, tmp_path):

    response = Mock()
    response.content = b"123456789"
    response.raise_for_status = Mock()

    mock_get.return_value = response

    photo = make_photo()

    d = Downloader()

    result = d.download([photo], tmp_path)

    assert len(result) == 1

    p = result[0]

    assert p.status == ImportStatus.SUCCESS
    assert p.local_path.exists()
    assert p.size == 9


# ---------------------------------------------------------
# SKIP EXISTING
# ---------------------------------------------------------

@patch("core.photo_import.downloader.requests.get")
def test_skip_existing(mock_get, tmp_path):

    (tmp_path / "photo.jpg").write_bytes(b"old")

    photo = make_photo()

    d = Downloader()

    result = d.download(
        [photo],
        tmp_path,
        skip_existing=True
    )

    assert result[0].status == ImportStatus.SKIP

    mock_get.assert_not_called()


# ---------------------------------------------------------
# NETWORK FAIL
# ---------------------------------------------------------

@patch("core.photo_import.downloader.requests.get")
def test_network_failure(mock_get, tmp_path):

    mock_get.side_effect = Exception("network error")

    photo = make_photo()

    d = Downloader(retries=2)

    result = d.download([photo], tmp_path)

    p = result[0]

    assert p.status == ImportStatus.FAILED
    assert p.error == "Не удалось получить файл"


# ---------------------------------------------------------
# SAVE ERROR
# ---------------------------------------------------------

@patch("core.photo_import.downloader.requests.get")
@patch("builtins.open")
def test_save_error(mock_open, mock_get, tmp_path):

    response = Mock()
    response.content = b"123"
    response.raise_for_status = Mock()

    mock_get.return_value = response

    mock_open.side_effect = PermissionError("permission denied")

    photo = make_photo()

    d = Downloader()

    result = d.download([photo], tmp_path)

    p = result[0]

    assert p.status == ImportStatus.FAILED
    assert "permission denied" in p.error.lower()


# ---------------------------------------------------------
# CANCEL BEFORE START
# ---------------------------------------------------------

def test_cancel_before_start(tmp_path):

    photo1 = make_photo("1.jpg")
    photo2 = make_photo("2.jpg")

    d = Downloader()

    d.cancel()

    result = d.download(
        [photo1, photo2],
        tmp_path
    )

    assert len(result) == 2

    assert all(
        p.status == ImportStatus.CANCELLED
        for p in result
    )


# ---------------------------------------------------------
# PROGRESS CALLBACK
# ---------------------------------------------------------

@patch("core.photo_import.downloader.requests.get")
def test_progress_callback(mock_get, tmp_path):

    response = Mock()
    response.content = b"123"
    response.raise_for_status = Mock()

    mock_get.return_value = response

    calls = []

    def progress(done, total, filename):
        calls.append((done, total, filename))

    photos = [
        make_photo("1.jpg"),
        make_photo("2.jpg"),
        make_photo("3.jpg"),
    ]

    d = Downloader()

    d.download(
        photos,
        tmp_path,
        on_progress=progress
    )

    assert len(calls) == 3

    assert calls[-1][0] == 3
    assert calls[-1][1] == 3


# ---------------------------------------------------------
# RETRIES
# ---------------------------------------------------------

@patch("core.photo_import.downloader.requests.get")
def test_retry_logic(mock_get, tmp_path):

    response = Mock()
    response.content = b"123"
    response.raise_for_status = Mock()

    mock_get.side_effect = [
        Exception(),
        Exception(),
        response,
    ]

    photo = make_photo()

    d = Downloader(retries=3)

    result = d.download([photo], tmp_path)

    assert result[0].status == ImportStatus.SUCCESS

    assert mock_get.call_count == 3