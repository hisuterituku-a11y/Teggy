from pathlib import Path
from unittest.mock import Mock

import pytest

from core.yandex.yandex_router import YandexRouter


@pytest.fixture
def router():
    """
    Создаёт маршрутизатор с отключённым выводом
    в консоль.
    """

    instance = YandexRouter()

    instance.log = Mock()
    instance.progress = Mock()

    return instance


def test_router_runs_required_stages_without_stories(
    router,
    tmp_path,
):
    """
    Без Stories всегда выполняются:

    1. Фото организации
    2. Фото отзывов
    3. Сравнение фотографий
    """

    router._download_organization_photos = Mock(
        return_value=10
    )

    router._download_review_photos = Mock(
        return_value=5
    )

    router._compare_photos = Mock()

    router._download_stories = Mock(
        return_value=3
    )

    result = router.run(
        url="https://yandex.ru/maps/org/test/",
        save_dir=tmp_path,
        download_stories=False,
        skip_existing=True,
    )

    assert result is True

    router._download_organization_photos.assert_called_once_with(
        gallery_url=(
            "https://yandex.ru/maps/org/test/gallery/"
        ),
        folder=Path(tmp_path) / "Фото организации",
        skip_existing=True,
    )

    router._download_review_photos.assert_called_once_with(
        reviews_url=(
            "https://yandex.ru/maps/org/test/reviews/"
        ),
        folder=Path(tmp_path) / "Фото отзывы",
        skip_existing=True,
    )

    router._compare_photos.assert_called_once_with(
        org_folder=Path(tmp_path) / "Фото организации",
        reviews_folder=Path(tmp_path) / "Фото отзывы",
    )

    router._download_stories.assert_not_called()


def test_router_runs_stories_when_enabled(
    router,
    tmp_path,
):
    """
    При включённой настройке Stories запускаются
    после сравнения фотографий.
    """

    call_order = []

    def download_organization(**kwargs):
        call_order.append(
            "organization"
        )
        return 10

    def download_reviews(**kwargs):
        call_order.append(
            "reviews"
        )
        return 5

    def compare_photos(**kwargs):
        call_order.append(
            "compare"
        )

    def download_stories(**kwargs):
        call_order.append(
            "stories"
        )
        return 3

    router._download_organization_photos = Mock(
        side_effect=download_organization
    )

    router._download_review_photos = Mock(
        side_effect=download_reviews
    )

    router._compare_photos = Mock(
        side_effect=compare_photos
    )

    router._download_stories = Mock(
        side_effect=download_stories
    )

    result = router.run(
        url="https://yandex.ru/maps/org/test/",
        save_dir=tmp_path,
        download_stories=True,
    )

    assert result is True

    assert call_order == [
        "organization",
        "reviews",
        "compare",
        "stories",
    ]


def test_router_always_compares_photos(
    router,
    tmp_path,
):
    """
    Сравнение запускается даже тогда, когда один
    из загрузчиков завершился ошибкой.
    """

    router._download_organization_photos = Mock(
        side_effect=RuntimeError(
            "Ошибка фото организации"
        )
    )

    router._download_review_photos = Mock(
        side_effect=RuntimeError(
            "Ошибка фото отзывов"
        )
    )

    router._compare_photos = Mock()

    router._download_stories = Mock()

    router._register_error = Mock(
        return_value="Тестовая ошибка"
    )

    result = router.run(
        url="https://yandex.ru/maps/org/test/",
        save_dir=tmp_path,
        download_stories=False,
    )

    assert result is True

    router._compare_photos.assert_called_once_with(
        org_folder=Path(tmp_path) / "Фото организации",
        reviews_folder=Path(tmp_path) / "Фото отзывы",
    )

    router._download_stories.assert_not_called()

    assert router._register_error.call_count == 2


def test_stories_error_does_not_fail_import(
    router,
    tmp_path,
):
    """
    Ошибка Stories не должна отменять успешно
    выполненные основные этапы.
    """

    router._download_organization_photos = Mock(
        return_value=10
    )

    router._download_review_photos = Mock(
        return_value=5
    )

    router._compare_photos = Mock()

    router._download_stories = Mock(
        side_effect=RuntimeError(
            "Stories недоступны"
        )
    )

    router._register_error = Mock(
        return_value="Ошибка Stories"
    )

    result = router.run(
        url="https://yandex.ru/maps/org/test/",
        save_dir=tmp_path,
        download_stories=True,
    )

    assert result is True

    router._register_error.assert_called_once()

    error_call = (
        router._register_error.call_args.kwargs
    )

    assert error_call["stage"] == "Stories"


def test_router_stops_after_cancellation(
    router,
    tmp_path,
):
    """
    После запроса отмены следующие этапы
    не запускаются.
    """

    def cancel_after_organization(**kwargs):
        router._cancelled = True
        return 10

    router._download_organization_photos = Mock(
        side_effect=cancel_after_organization
    )

    router._download_review_photos = Mock(
        return_value=5
    )

    router._compare_photos = Mock()
    router._download_stories = Mock()

    result = router.run(
        url="https://yandex.ru/maps/org/test/",
        save_dir=tmp_path,
        download_stories=True,
    )

    assert result is False

    router._download_organization_photos.assert_called_once()
    router._download_review_photos.assert_not_called()
    router._compare_photos.assert_not_called()
    router._download_stories.assert_not_called()


def test_router_creates_required_folders_without_stories(
    router,
    tmp_path,
):
    """
    Без Stories создаются только обязательные папки.
    """

    router._download_organization_photos = Mock(
        return_value=0
    )

    router._download_review_photos = Mock(
        return_value=0
    )

    router._compare_photos = Mock()
    router._download_stories = Mock()

    result = router.run(
        url="https://yandex.ru/maps/org/test/",
        save_dir=tmp_path,
        download_stories=False,
    )

    assert result is True

    assert (
        Path(tmp_path) / "Фото организации"
    ).is_dir()

    assert (
        Path(tmp_path) / "Фото отзывы"
    ).is_dir()

    assert not (
        Path(tmp_path) / "Сторис"
    ).exists()


def test_router_creates_stories_folder_when_enabled(
    router,
    tmp_path,
):
    """
    Папка Stories создаётся только при включённой
    настройке загрузки.
    """

    router._download_organization_photos = Mock(
        return_value=0
    )

    router._download_review_photos = Mock(
        return_value=0
    )

    router._compare_photos = Mock()

    router._download_stories = Mock(
        return_value=0
    )

    result = router.run(
        url="https://yandex.ru/maps/org/test/",
        save_dir=tmp_path,
        download_stories=True,
    )

    assert result is True

    assert (
        Path(tmp_path) / "Сторис"
    ).is_dir()

    router._download_stories.assert_called_once_with(
        base_url="https://yandex.ru/maps/org/test",
        folder=Path(tmp_path) / "Сторис",
        skip_existing=True,
    )


@pytest.mark.parametrize(
    (
        "source_url",
        "expected_base_url",
    ),
    [
        (
            "https://yandex.ru/maps/org/test/",
            "https://yandex.ru/maps/org/test",
        ),
        (
            "https://yandex.ru/maps/org/test/gallery/",
            "https://yandex.ru/maps/org/test",
        ),
        (
            "https://yandex.ru/maps/org/test/reviews/",
            "https://yandex.ru/maps/org/test",
        ),
        (
            "https://yandex.ru/maps/org/test/?ll=1%2C2",
            "https://yandex.ru/maps/org/test",
        ),
    ],
)
def test_router_normalizes_organization_url(
    source_url,
    expected_base_url,
):
    """
    Router удаляет gallery, reviews и параметры
    из ссылки организации.
    """

    result = YandexRouter._normalize_base_url(
        source_url
    )

    assert result == expected_base_url


def test_router_rejects_empty_url():
    """
    Пустая ссылка не должна запускать импорт.
    """

    with pytest.raises(
        ValueError,
        match="Не указана ссылка",
    ):
        YandexRouter._normalize_base_url(
            "   "
        )