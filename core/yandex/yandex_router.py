from pathlib import Path

from core.yandex.photo_compare import PhotoComparator
from core.yandex.yandex_downloader import YandexPhotoDownloader
from core.yandex.yandex_reviews import YandexReviewDownloader
from core.yandex.yandex_stories import YandexStoriesDownloader


class YandexRouter:
    def log(self, text: str) -> None:
        print(f"[YandexRouter] {text}")

    def run(self, url: str, save_dir: Path | str) -> None:
        save_dir = Path(save_dir)

        # Создаём рабочие папки
        org_folder = save_dir / "Фото организации"
        reviews_folder = save_dir / "Фото отзывы"
        stories_folder = save_dir / "Сторис"

        org_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        reviews_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        stories_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        base_url = (
            url
            .split("/gallery")[0]
            .split("/reviews")[0]
            .split("?")[0]
            .rstrip("/")
        )

        gallery_url = f"{base_url}/gallery/"
        reviews_url = f"{base_url}/reviews/"

        self.log("Организация:")
        self.log(base_url)

        # ==================================================
        # СТОРИС
        # ==================================================

        self.log("Запускаем сбор сторис")

        story_downloader = YandexStoriesDownloader()

        stories = story_downloader.collect(base_url)

        story_downloader.download(
            stories,
            stories_folder,
        )

        self.log(
            f"Сторис скачано: {len(stories)}"
        )

        # ==================================================
        # ФОТО ОРГАНИЗАЦИИ
        # ==================================================

        self.log("Открываем галерею организации")
        self.log(gallery_url)
        self.log("Запускаем сбор фото организации")

        photo_downloader = YandexPhotoDownloader(
            headless=False,
        )

        org_photos = photo_downloader.collect(
            gallery_url,
        )

        photo_downloader.download(
            org_photos,
            folder=org_folder,
        )

        self.log(
            f"Фото организации скачано: {len(org_photos)}"
        )

        # ==================================================
        # ФОТО ОТЗЫВОВ
        # ==================================================

        self.log("Открываем отзывы")
        self.log(reviews_url)
        self.log("Запускаем сбор фото отзывов")

        review_downloader = YandexReviewDownloader(
            headless=False,
        )

        review_photos = review_downloader.collect(
            reviews_url,
        )

        review_downloader.download(
            review_photos,
            folder=reviews_folder,
        )

        self.log(
            f"Фото отзывов скачано: {len(review_photos)}"
        )

        # ==================================================
        # СРАВНЕНИЕ
        # ==================================================

        self.log(
            "Сравниваем фото организации и отзывы"
        )

        comparator = PhotoComparator(
            org_folder=org_folder,
            reviews_folder=reviews_folder,
        )

        comparator.compare()

        # ==================================================
        # ФИНИШ
        # ==================================================

        self.log("================================")
        self.log("ГОТОВО")

        self.log(
            f"Организация: {len(org_photos)} фото"
        )

        self.log(
            f"Отзывы: {len(review_photos)} фото"
        )

        self.log(
            f"Сторис: {len(stories)}"
        )

        self.log(
            "Дубли удалены из папки организации"
        )

        self.log("================================")


if __name__ == "__main__":
    url = input(
        "\nСсылка Яндекс организации:\n> "
    ).strip()

    save_dir = input(
        "\nПапка сохранения:\n> "
    ).strip()

    router = YandexRouter()

    router.run(
        url=url,
        save_dir=save_dir,
    )