from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Callable

import requests
from playwright.sync_api import Browser, sync_playwright


LogCallback = Callable[[str], None]


class YandexReviewDownloader:
    """Сборщик фотографий из отзывов организации Яндекс Карт."""

    def __init__(self, headless: bool = False, timeout: int = 60):
        self.headless = headless
        self.timeout = timeout

        self._cancelled = False
        self._browser: Browser | None = None

    def _log(
        self,
        text: str,
        on_log: LogCallback | None = None,
    ) -> None:
        if on_log:
            on_log(text)
        else:
            print(f"[YandexReviews] {text}")

    @staticmethod
    def _normalize_reviews_url(url: str) -> str:
        clean_url = url.strip()

        if not clean_url:
            raise ValueError("Не указана ссылка на организацию")

        if "?" in clean_url:
            base, params = clean_url.split("?", 1)
            query = f"?{params}"
        else:
            base = clean_url
            query = ""

        base = (
            base
            .split("/gallery", 1)[0]
            .split("/reviews", 1)[0]
            .rstrip("/")
        )

        return f"{base}/reviews/{query}"

    @staticmethod
    def _normalize_photo_url(url: str) -> str | None:
        if "avatars.mds.yandex.net" not in url:
            return None

        clean_url = url.split("?", 1)[0]

        blocked_fragments = (
            "get-vh",
            "get-maps_stories",
            "get-yapic",
            "get-direct",
            "get-bunker",
            "get-tycoon",
        )

        if any(fragment in clean_url for fragment in blocked_fragments):
            return None

        size_suffixes = (
            "/S",
            "/M",
            "/L",
            "/XL",
            "/XXL",
            "/XXXL",
        )

        for suffix in size_suffixes:
            if clean_url.endswith(suffix):
                return clean_url[:-len(suffix)] + "/XXXL"

        return clean_url

    def collect(
        self,
        url: str,
        on_log: LogCallback | None = None,
    ) -> list[str]:
        self._cancelled = False

        photos: list[str] = []
        photo_keys: set[str] = set()
        browser: Browser | None = None

        reviews_url = self._normalize_reviews_url(url)

        try:
            with sync_playwright() as playwright:
                self._log("Запуск браузера", on_log)

                browser = playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                    ],
                )
                self._browser = browser

                context = browser.new_context(
                    viewport={
                        "width": 1920,
                        "height": 1080,
                    },
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/120 Safari/537.36"
                    ),
                )

                page = context.new_page()

                def handle_response(response) -> None:
                    if self._cancelled:
                        return

                    try:
                        photo_url = self._normalize_photo_url(response.url)

                        if not photo_url:
                            return

                        if photo_url in photo_keys:
                            return

                        photo_keys.add(photo_url)
                        photos.append(photo_url)

                        self._log(
                            f"Фото из отзывов найдено: {len(photos)}",
                            on_log,
                        )

                    except Exception:
                        return

                page.on("response", handle_response)

                self._log(
                    f"Открываем отзывы: {reviews_url}",
                    on_log,
                )

                page.goto(
                    reviews_url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout * 1000,
                )

                page.wait_for_timeout(5000)

                if self._cancelled:
                    self._log("Сбор фото отзывов отменён", on_log)
                    return photos

                self._log(
                    "Начинаем прокрутку отзывов",
                    on_log,
                )

                no_new_counter = 0

                for step in range(300):
                    if self._cancelled:
                        self._log(
                            "Сбор фото отзывов отменён",
                            on_log,
                        )
                        break

                    before = len(photos)

                    page.mouse.wheel(
                        0,
                        random.randint(700, 1200),
                    )

                    page.wait_for_timeout(
                        random.randint(300, 700),
                    )

                    after = len(photos)

                    if after == before:
                        no_new_counter += 1
                    else:
                        no_new_counter = 0

                    self._log(
                        (
                            f"Отзывы: шаг {step + 1}/300, "
                            f"фото: {after}"
                        ),
                        on_log,
                    )

                    if no_new_counter < 10:
                        continue

                    self._log(
                        "Проверяем финальную догрузку отзывов",
                        on_log,
                    )

                    page.wait_for_timeout(5000)

                    if len(photos) == after:
                        break

                    no_new_counter = 0

        finally:
            self._browser = None

            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass

        self._log(
            f"Сбор фото отзывов завершён: {len(photos)}",
            on_log,
        )

        return photos

    def save_json(
        self,
        urls: list[str],
        filename: Path | str = "reviews_urls.json",
        on_log: LogCallback | None = None,
    ) -> None:
        filename = Path(filename)

        filename.write_text(
            json.dumps(
                urls,
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )

        self._log(
            f"Ссылки сохранены: {filename}",
            on_log,
        )

    def download(
        self,
        urls: list[str],
        folder: Path | str = "reviews_photos",
        on_log: LogCallback | None = None,
        skip_existing: bool = True,
    ) -> int:
        folder = Path(folder)
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        session = requests.Session()
        total = len(urls)

        saved = 0
        skipped = 0

        for index, url in enumerate(urls, start=1):
            if self._cancelled:
                self._log(
                    "Скачивание фото отзывов отменено",
                    on_log,
                )
                break

            filename = folder / f"{index:03}.jpg"

            if (
                skip_existing
                and filename.exists()
                and filename.stat().st_size > 0
            ):
                skipped += 1

                self._log(
                    f"Фото отзывов {index}/{total}: уже существует",
                    on_log,
                )
                continue

            try:
                response = session.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                    },
                    timeout=30,
                )
                response.raise_for_status()

                filename.write_bytes(response.content)
                saved += 1

                self._log(
                    f"Фото отзывов скачано: {index}/{total}",
                    on_log,
                )

            except Exception as exc:
                self._log(
                    f"Ошибка скачивания фото отзывов {index}: {exc}",
                    on_log,
                )

        self._log(
            (
                f"Фото отзывов сохранено: {saved}; "
                f"пропущено существующих: {skipped}"
            ),
            on_log,
        )

        return saved

    def cancel(self) -> None:
        self._cancelled = True

        browser = self._browser

        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
