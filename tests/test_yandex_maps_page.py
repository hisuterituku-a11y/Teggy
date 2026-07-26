from pathlib import Path
from unittest.mock import Mock

import pytest

from gui.pages.yandex_maps import YandexMapsPage


@pytest.fixture
def page(qtbot):
    """
    Создаёт страницу Яндекс Карт для каждого теста.
    """

    widget = YandexMapsPage()

    qtbot.addWidget(widget)

    return widget


def test_download_button_disabled_without_required_fields(
    page,
):
    """
    Кнопка недоступна, пока не указаны ссылка и папка.
    """

    assert page.download_button.isEnabled() is False

    page.url_input.setText(
        "https://yandex.ru/maps/org/test/"
    )

    page.update_download_button()

    assert page.download_button.isEnabled() is False


def test_download_button_enabled_when_url_and_folder_exist(
    page,
    tmp_path,
):
    """
    Кнопка становится доступна после заполнения
    ссылки и выбора папки.
    """

    page.url_input.setText(
        "https://yandex.ru/maps/org/test/"
    )

    page.output_folder = Path(tmp_path)

    page.folder_path_input.setText(
        str(tmp_path)
    )

    page.update_download_button()

    assert page.download_button.isEnabled() is True
    assert page.download_status.text() == (
        "Данные готовы к загрузке"
    )


@pytest.mark.parametrize(
    (
        "stories_checked",
        "expected_download_stories",
    ),
    [
        (False, False),
        (True, True),
    ],
)
def test_start_download_passes_correct_parameters_to_service(
    page,
    tmp_path,
    stories_checked,
    expected_download_stories,
):
    """
    Проверяет передачу URL, папки и настройки Stories
    в YandexService.
    """

    service_start = Mock()

    page.service.start = service_start

    url = "https://yandex.ru/maps/org/test/"

    page.url_input.setText(
        url
    )

    page.output_folder = Path(tmp_path)

    page.folder_path_input.setText(
        str(tmp_path)
    )

    page.stories_checkbox.setChecked(
        stories_checked
    )

    page.update_download_button()
    page.start_download()

    service_start.assert_called_once()

    call_kwargs = service_start.call_args.kwargs

    assert call_kwargs["url"] == url
    assert call_kwargs["save_dir"] == Path(tmp_path)
    assert (
        call_kwargs["download_stories"]
        is expected_download_stories
    )
    assert call_kwargs["skip_existing"] is True

    assert (
        call_kwargs["on_log"]
        == page.append_download_log
    )

    assert (
        call_kwargs["on_progress"]
        == page.update_download_progress
    )

    assert (
        call_kwargs["on_finished"]
        == page.on_download_finished
    )


def test_start_download_locks_interface(
    page,
    tmp_path,
    qtbot,
):
    """
    После запуска поля и кнопки блокируются,
    а индикатор становится видимым.
    """

    page.service.start = Mock()

    page.url_input.setText(
        "https://yandex.ru/maps/org/test/"
    )

    page.output_folder = Path(tmp_path)

    page.folder_path_input.setText(
        str(tmp_path)
    )

    page.show()
    qtbot.waitExposed(page)

    page.update_download_button()
    page.start_download()

    assert page.download_button.isEnabled() is False
    assert page.folder_button.isEnabled() is False
    assert page.check_button.isEnabled() is False
    assert page.url_input.isEnabled() is False
    assert page.stories_checkbox.isEnabled() is False

    assert page.download_progress.isVisible() is True
    assert page.download_status.text() == (
        "Загрузка запущена"
    )


def test_finished_success_restores_interface(
    page,
    tmp_path,
):
    """
    После успешного завершения интерфейс возвращается
    в обычное состояние.
    """

    page.url_input.setText(
        "https://yandex.ru/maps/org/test/"
    )

    page.output_folder = Path(tmp_path)

    page.folder_path_input.setText(
        str(tmp_path)
    )

    page.download_progress.setVisible(
        True
    )

    page.folder_button.setEnabled(
        False
    )

    page.check_button.setEnabled(
        False
    )

    page.url_input.setEnabled(
        False
    )

    page.stories_checkbox.setEnabled(
        False
    )

    page.on_download_finished(
        True
    )

    assert page.download_progress.isVisible() is False
    assert page.folder_button.isEnabled() is True
    assert page.check_button.isEnabled() is True
    assert page.url_input.isEnabled() is True
    assert page.stories_checkbox.isEnabled() is True
    assert page.download_button.isEnabled() is True

    assert page.download_status.text() == (
        "Данные готовы к загрузке"
    )


def test_finished_failure_restores_interface(
    page,
    tmp_path,
):
    """
    После ошибки интерфейс также должен разблокироваться.
    """

    page.url_input.setText(
        "https://yandex.ru/maps/org/test/"
    )

    page.output_folder = Path(tmp_path)

    page.folder_path_input.setText(
        str(tmp_path)
    )

    page.on_download_finished(
        False
    )

    assert page.folder_button.isEnabled() is True
    assert page.check_button.isEnabled() is True
    assert page.url_input.isEnabled() is True
    assert page.stories_checkbox.isEnabled() is True
    assert page.download_button.isEnabled() is True


def test_log_message_is_added_to_download_log(
    page,
):
    """
    Сообщения backend отображаются в журнале.
    """

    page.append_download_log(
        "Тестовое сообщение"
    )

    assert "Тестовое сообщение" in (
        page.download_log.toPlainText()
    )


def test_progress_message_updates_status(
    page,
):
    """
    Название текущего этапа выводится в статус.
    """

    page.update_download_progress(
        "Фото организации"
    )

    assert page.download_status.text() == (
        "Фото организации"
    )