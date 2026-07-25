from __future__ import annotations

from pathlib import Path

from core.worker_thread import ProcessingThread


class FakeWorker:
    def __init__(self, stats: dict | None = None) -> None:
        self.stats = stats or {
            "total": 1,
            "processed": 1,
            "converted": 0,
            "failed": 0,
            "errors": [],
        }
        self.metadata = None
        self.tags = None
        self.options = None
        self.callbacks = None
        self.file_list_call = None
        self.folder_call = None

    def set_metadata(self, **metadata) -> None:
        self.metadata = metadata

    def set_tags(self, tags) -> None:
        self.tags = tags

    def set_processing_options(self, **options) -> None:
        self.options = options

    def set_callbacks(self, **callbacks) -> None:
        self.callbacks = callbacks

    def process_file_list(self, file_list, output_dir=None):
        self.file_list_call = (file_list, output_dir)
        return self.stats

    def process_folder(self, folder_path, output_dir=None):
        self.folder_call = (folder_path, output_dir)
        return self.stats


def test_setup_stores_processing_parameters() -> None:
    thread = ProcessingThread()
    files = [Path("photo.jpg")]

    thread.setup(
        folder_path="X:/Photos",
        file_list=files,
        metadata={"title": "Клиника"},
        tags=["Тег;tag"],
        delete_original=True,
        quality=88,
        output_dir="X:/Output",
    )

    assert thread.folder_path == "X:/Photos"
    assert thread.file_list == files
    assert thread.metadata == {"title": "Клиника"}
    assert thread.tags == ["Тег;tag"]
    assert thread.delete_original is True
    assert thread.quality == 88
    assert thread.output_dir == "X:/Output"


def test_cancel_sets_flag() -> None:
    thread = ProcessingThread()

    thread.cancel()

    assert thread._is_cancelled is True


def test_run_uses_file_list_and_emits_stats() -> None:
    thread = ProcessingThread()
    fake_worker = FakeWorker()
    thread.worker = fake_worker
    files = [Path("X:/Photos/photo.jpg")]
    emitted: list[dict] = []
    thread.finished.connect(emitted.append)

    thread.setup(
        folder_path="X:/Photos",
        file_list=files,
        metadata={"title": "Клиника"},
        tags=["Тег;tag"],
        delete_original=True,
        quality=91,
    )
    thread.run()

    assert fake_worker.metadata == {"title": "Клиника"}
    assert fake_worker.tags == ["Тег;tag"]
    assert fake_worker.options == {
        "delete_original": True,
        "quality": 91,
    }
    assert fake_worker.file_list_call == (
        files,
        str(Path("X:/Photos") / "Teggy"),
    )
    assert emitted == [fake_worker.stats]


def test_run_emits_cancelled_result() -> None:
    thread = ProcessingThread()
    thread.worker = FakeWorker()
    emitted: list[dict] = []
    thread.finished.connect(emitted.append)
    thread.setup(
        folder_path="X:/Photos",
        file_list=[Path("photo.jpg")],
        tags=["Тег;tag"],
    )
    thread.cancel()

    thread.run()

    assert emitted == [{"cancelled": True}]
