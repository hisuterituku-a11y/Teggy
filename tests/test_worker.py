from __future__ import annotations

from pathlib import Path

import pytest

import core.worker as worker_module
from core.exceptions import TegiError


class FakeMetadataWriter:
    def __init__(self) -> None:
        self.metadata_calls: list[dict] = []
        self.written_files: list[Path] = []

    def set_metadata(self, **kwargs) -> None:
        self.metadata_calls.append(kwargs)

    def write(self, file_path: Path) -> None:
        self.written_files.append(Path(file_path))


@pytest.fixture
def worker(monkeypatch):
    monkeypatch.setattr(worker_module, "MetadataWriter", FakeMetadataWriter)
    return worker_module.ProcessingWorker()


def test_worker_defaults(worker) -> None:
    assert worker.tags == []
    assert worker.delete_original is False
    assert worker.quality == 100


def test_worker_configuration(worker) -> None:
    worker.set_metadata(title="Клиника", rating=5)
    worker.set_tags(["Стоматология;stomatologiya"])
    worker.set_processing_options(delete_original=True, quality=87)

    assert worker.metadata_writer.metadata_calls == [
        {"title": "Клиника", "rating": 5}
    ]
    assert worker.tags == ["Стоматология;stomatologiya"]
    assert worker.delete_original is True
    assert worker.quality == 87


def test_callbacks_receive_log_and_progress(worker) -> None:
    logs: list[str] = []
    progress: list[tuple[int, int]] = []
    worker.set_callbacks(
        on_log=logs.append,
        on_progress=lambda current, total: progress.append((current, total)),
    )

    worker._log("message")
    worker._progress(2, 5)

    assert logs == ["message"]
    assert progress == [(2, 5)]


def test_process_folder_raises_for_missing_folder(worker, tmp_path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(TegiError, match="Папка не найдена"):
        worker.process_folder(str(missing))


def test_process_folder_returns_empty_stats_without_images(worker, tmp_path) -> None:
    logs: list[str] = []
    worker.set_callbacks(on_log=logs.append)

    result = worker.process_folder(str(tmp_path))

    assert result == {
        "total": 0,
        "processed": 0,
        "converted": 0,
        "failed": 0,
        "errors": [],
    }
    assert any("Нет поддерживаемых файлов" in message for message in logs)


def test_process_file_list_requires_tags(worker, tmp_path) -> None:
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"jpeg")

    result = worker.process_file_list([source])

    assert result == {
        "total": 1,
        "processed": 0,
        "converted": 0,
        "failed": 0,
        "errors": ["Теги не заданы"],
    }


def test_process_file_list_writes_metadata_and_reports_progress(
    worker, tmp_path, monkeypatch
) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_bytes(b"jpeg")
    second.write_bytes(b"jpeg")

    monkeypatch.setattr(
        worker_module.ImageConverter,
        "needs_conversion",
        staticmethod(lambda path: False),
    )

    progress: list[tuple[int, int]] = []
    worker.set_callbacks(
        on_progress=lambda current, total: progress.append((current, total))
    )
    worker.set_tags(["Первый;pervyj", "Второй;vtoroj"])

    result = worker.process_file_list(
        [first, second],
        output_dir=str(tmp_path / "output"),
    )

    assert result == {
        "total": 2,
        "processed": 2,
        "converted": 0,
        "failed": 0,
        "errors": [],
    }
    assert worker.metadata_writer.metadata_calls == [
        {"keywords": "Первый;pervyj"},
        {"keywords": "Второй;vtoroj"},
    ]
    assert worker.metadata_writer.written_files == [first, second]
    assert progress == [(1, 2), (2, 2)]


def test_process_single_requires_existing_file(worker, tmp_path) -> None:
    with pytest.raises(TegiError, match="Файл не найден"):
        worker.process_single(str(tmp_path / "missing.jpg"))


def test_process_single_requires_tags(worker, tmp_path) -> None:
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"jpeg")

    with pytest.raises(TegiError, match="Теги не заданы"):
        worker.process_single(str(source))
