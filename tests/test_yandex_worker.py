from pathlib import Path
from unittest.mock import Mock, patch

from core.yandex.worker import YandexWorker


def test_worker_passes_arguments_to_router(tmp_path):
    """
    Worker должен передать все параметры в Router.
    """

    router = Mock()
    router.run.return_value = True

    with patch(
        "core.yandex.worker.YandexRouter",
        return_value=router,
    ):
        worker = YandexWorker(
            url="https://yandex.ru/maps/org/test/",
            save_dir=tmp_path,
            download_stories=True,
            skip_existing=False,
        )

        worker.run()

    router.run.assert_called_once()

    kwargs = router.run.call_args.kwargs

    assert kwargs["save_dir"] == Path(tmp_path)
    assert kwargs["download_stories"] is True
    assert kwargs["skip_existing"] is False


def test_worker_calls_finished_true(
    tmp_path,
    qtbot,
):
    """
    При успешной работе finished(True)
    отправляется обязательно.
    """

    router = Mock()
    router.run.return_value = True

    with patch(
        "core.yandex.worker.YandexRouter",
        return_value=router,
    ):
        worker = YandexWorker(
            url="url",
            save_dir=tmp_path,
        )

        with qtbot.waitSignal(
            worker.finished,
            timeout=1000,
        ) as signal:
            worker.run()

    assert signal.args == [True]


def test_worker_calls_finished_false_on_exception(
    tmp_path,
    qtbot,
):
    """
    Даже при исключении должен прийти
    finished(False).
    """

    with patch(
        "core.yandex.worker.YandexRouter",
        side_effect=RuntimeError("boom"),
    ), patch(
        "core.yandex.worker.save_diagnostic_report",
        return_value=tmp_path,
    ):

        worker = YandexWorker(
            url="url",
            save_dir=tmp_path,
        )

        with qtbot.waitSignal(
            worker.finished,
            timeout=1000,
        ) as signal:
            worker.run()

    assert signal.args == [False]


def test_worker_saves_diagnostic_report(
    tmp_path,
    qtbot,
):
    """
    При ошибке создаётся диагностика.
    """

    with patch(
        "core.yandex.worker.YandexRouter",
        side_effect=RuntimeError("boom"),
    ), patch(
        "core.yandex.worker.save_diagnostic_report",
        return_value=tmp_path,
    ) as save_report:

        worker = YandexWorker(
            url="url",
            save_dir=tmp_path,
        )

        with qtbot.waitSignal(
            worker.finished,
            timeout=1000,
        ):
            worker.run()

    save_report.assert_called_once()


def test_cancel_without_router():
    """
    cancel() безопасен,
    если Router ещё не создан.
    """

    worker = YandexWorker(
        url="url",
        save_dir=".",
    )

    worker.requestInterruption = Mock()

    worker.cancel()

    assert worker._cancel_requested is True

    worker.requestInterruption.assert_called_once()


def test_cancel_calls_router_cancel(tmp_path):
    """
    Если Router уже работает,
    cancel() должен его остановить.
    """

    router = Mock()

    worker = YandexWorker(
        url="url",
        save_dir=tmp_path,
    )

    worker._router = router

    worker.requestInterruption = Mock()

    worker.cancel()

    router.cancel.assert_called_once()

    worker.requestInterruption.assert_called_once()


def test_worker_connects_callbacks(tmp_path):
    """
    Переданные callback должны
    подключаться к Qt-сигналам.
    """

    log = Mock()
    progress = Mock()
    finished = Mock()

    worker = YandexWorker(
        url="url",
        save_dir=tmp_path,
        on_log=log,
        on_progress=progress,
        on_finished=finished,
    )

    worker.log.emit("hello")
    worker.progress.emit("stage")
    worker.finished.emit(True)

    log.assert_called_once_with("hello")
    progress.assert_called_once_with("stage")
    finished.assert_called_once_with(True)