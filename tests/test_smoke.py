from __future__ import annotations


def test_core_modules_import() -> None:
    from core.settings import Settings
    from core.tag_generator import TagGenerator
    from core.worker import ProcessingWorker
    from core.worker_thread import ProcessingThread

    assert Settings is not None
    assert TagGenerator is not None
    assert ProcessingWorker is not None
    assert ProcessingThread is not None


def test_metadata_service_import() -> None:
    from core.metadata.metadata_service import MetadataService

    assert MetadataService is not None
