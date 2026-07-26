from pathlib import Path
from unittest.mock import Mock, patch

from core.yandex.service import YandexService


def test_start_creates_worker(tmp_path):
    """
    Service создаёт YandexWorker
    и сразу запускает его.
    """

    worker = Mock()

    with patch(
        "core.yandex.service.YandexWorker",
        return_value=worker,
    ) as worker_cls:

        service = YandexService()

        result = service.start(
            url="https://yandex.ru/maps/org/test/",
            save_dir=tmp_path,
            download_stories=True,
            skip_existing=False,
        )

    worker_cls.assert_called_once()

    kwargs = worker_cls.call_args.kwargs

    assert kwargs["url"] == "https://yandex.ru/maps/org/test/"
    assert kwargs["save_dir"] == Path(tmp_path)
    assert kwargs["download_stories"] is True
    assert kwargs["skip_existing"] is False

    worker.start.assert_called_once()

    assert result is worker


def test_cancel_calls_worker_cancel():
    """
    cancel() должен вызвать
    cancel() рабочего потока.
    """

    service = YandexService()

    worker = Mock()

    service.worker = worker

    service.cancel()

    worker.cancel.assert_called_once()


def test_cancel_without_worker():
    """
    cancel() безопасен,
    даже если поток ещё не создан.
    """

    service = YandexService()

    service.worker = None

    service.cancel()