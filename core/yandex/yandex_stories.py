from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Callable

import requests
from playwright.sync_api import Browser, Page, sync_playwright


LogCallback = Callable[[str], None]


class YandexStoriesDownloader:
    """Сборщик изображений из Stories организации Яндекс Карт."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30,
    ):
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
            print(f"[Stories] {text}")

    @staticmethod
    def _story_key(url: str) -> str:
        clean_url = url.split("?", 1)[0]

        if clean_url.endswith("/orig"):
            return clean_url[:-len("/orig")]

        parts = clean_url.rsplit("/", 1)

        if (
            len(parts) == 2
            and re.fullmatch(r"\d+x\d+", parts[1])
        ):
            return parts[0]

        return clean_url

    @staticmethod
    def _is_story_image(url: str) -> bool:
        clean_url = url.split("?", 1)[0]

        if "get-maps_stories" not in clean_url:
            return False

        last_segment = clean_url.rsplit("/", 1)[-1]

        return (
            last_segment == "orig"
            or bool(re.fullmatch(r"\d+x\d+", last_segment))
        )

    @staticmethod
    def _carousel_state(page: Page) -> tuple[str, ...]:
        """Возвращает состояние видимых обложек Stories слева направо."""
        try:
            items = page.evaluate(
                """
                () => {
                    const carousel = document.querySelector(
                        ".business-stories-view__carousel"
                    );

                    if (!carousel) return [];

                    const cr = carousel.getBoundingClientRect();

                    return [...document.querySelectorAll(".story-cover-preview")]
                        .map((el) => {
                            const r = el.getBoundingClientRect();

                            const visible = (
                                r.width > 0 &&
                                r.height > 0 &&
                                r.right > cr.left &&
                                r.left < cr.right
                            );

                            if (!visible) return null;

                            const inner = el.querySelector(
                                ".story-cover-preview__inner"
                            );

                            const background = inner
                                ? getComputedStyle(inner).backgroundImage
                                : "";

                            const img = el.querySelector("img");
                            const src = img
                                ? (
                                    img.currentSrc ||
                                    img.src ||
                                    img.getAttribute("src") ||
                                    ""
                                )
                                : "";

                            return {
                                x: r.x,
                                key: background || src || el.outerHTML.slice(0, 500)
                            };
                        })
                        .filter(Boolean)
                        .sort((a, b) => a.x - b.x)
                        .map((item) => item.key);
                }
                """
            )

            return tuple(str(item) for item in items)

        except Exception:
            return ()

    @staticmethod
    def _carousel_arrow(
        page: Page,
        direction: str,
    ):
        side = "_next" if direction == "next" else "_prev"

        return page.locator(
            ".business-stories-view__carousel "
            f".carousel__arrow-wrapper.{side} "
            ".carousel__arrow"
        ).first

    def _click_carousel_arrow(
        self,
        page: Page,
        direction: str,
    ) -> bool:
        """Нажимает точную стрелку ленты и ждёт изменения обложек."""
        try:
            arrow = self._carousel_arrow(page, direction)

            if arrow.count() == 0 or not arrow.is_visible():
                return False

            before = self._carousel_state(page)

            arrow.click(
                force=True,
                timeout=3000,
            )

            for _ in range(20):
                page.wait_for_timeout(100)
                after = self._carousel_state(page)

                if after and after != before:
                    return True

            return False

        except Exception:
            return False

    def _preload_story_covers(
        self,
        page: Page,
        on_log: LogCallback | None = None,
        max_steps: int = 50,
    ) -> None:
        """Пролистывает ленту обложек до конца и возвращает в начало."""
        self._log(
            "Пролистываем ленту обложек до конца",
            on_log,
        )

        right_steps = 0

        while (
            not self._cancelled
            and right_steps < max_steps
            and self._click_carousel_arrow(page, "next")
        ):
            right_steps += 1

            self._log(
                f"Лента вправо: шаг {right_steps}",
                on_log,
            )

            page.wait_for_timeout(250)

        self._log(
            "Возвращаем ленту в начало",
            on_log,
        )

        left_steps = 0

        while (
            not self._cancelled
            and left_steps < max_steps
            and self._click_carousel_arrow(page, "prev")
        ):
            left_steps += 1
            page.wait_for_timeout(250)

    def _nudge(
        self,
        page: Page,
        on_log: LogCallback | None = None,
    ) -> bool:
        try:
            page.keyboard.press("ArrowRight")

            self._log(
                "Переключаем Stories клавишей вправо",
                on_log,
            )
            return True

        except Exception:
            pass

        selectors = (
            ".story-screen-view__next",
            "[aria-label='Следующая история']",
            "[aria-label='Next story']",
        )

        for selector in selectors:
            try:
                button = page.locator(selector).first

                if button.count() > 0:
                    button.click(
                        force=True,
                        timeout=1500,
                    )

                    self._log(
                        "Переключаем Stories кнопкой Далее",
                        on_log,
                    )
                    return True

            except Exception:
                continue

        self._log(
            "Не удалось переключить Stories",
            on_log,
        )
        return False

    def collect(
        self,
        url: str,
        on_log: LogCallback | None = None,
        max_wait_seconds: float = 480.0,
        stall_threshold: float = 10.0,
        max_nudges: int = 12,
        final_stall_after_nudge: float = 15.0,
    ) -> list[str]:
        self._cancelled = False

        story_registry: dict[str, str] = {}
        story_order: list[str] = []

        browser: Browser | None = None

        def add_url(image_url: str) -> None:
            if not self._is_story_image(image_url):
                return

            clean_url = image_url.split("?", 1)[0]
            key = self._story_key(clean_url)

            current = story_registry.get(key)

            if current is None:
                story_order.append(key)
                story_registry[key] = clean_url

                self._log(
                    f"Stories найдено: {len(story_order)}",
                    on_log,
                )
                return

            if (
                clean_url.endswith("/orig")
                and not current.endswith("/orig")
            ):
                story_registry[key] = clean_url

        try:
            with sync_playwright() as playwright:
                self._log(
                    "Открываем Яндекс Карты для сбора Stories",
                    on_log,
                )

                browser = playwright.chromium.launch(
                    headless=self.headless,
                )
                self._browser = browser

                context = browser.new_context(
                    viewport={
                        "width": 1400,
                        "height": 900,
                    },
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/120 Safari/537.36"
                    ),
                )

                page = context.new_page()

                def response_handler(response) -> None:
                    if self._cancelled:
                        return

                    try:
                        add_url(response.url)
                    except Exception:
                        return

                page.on("response", response_handler)

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout * 1000,
                )

                page.wait_for_timeout(5000)

                if self._cancelled:
                    self._log(
                        "Сбор Stories отменён",
                        on_log,
                    )
                    return []

                self._preload_story_covers(
                    page,
                    on_log,
                )

                if self._cancelled:
                    self._log(
                        "Сбор Stories отменён",
                        on_log,
                    )
                    return []

                cards = page.locator(
                    ".story-cover-preview",
                )
                cards_count = cards.count()

                self._log(
                    f"Карточек Stories в DOM: {cards_count}",
                    on_log,
                )

                if cards_count == 0:
                    self._log(
                        "Stories у организации не найдены",
                        on_log,
                    )
                    return []

                try:
                    cards.first.click(
                        force=True,
                        timeout=5000,
                    )

                    self._log(
                        "Просмотрщик Stories открыт",
                        on_log,
                    )

                except Exception as exc:
                    self._log(
                        f"Не удалось открыть Stories: {exc}",
                        on_log,
                    )
                    return []

                started_at = time.monotonic()
                last_growth_at = started_at
                last_count = 0

                nudges_done = 0
                last_nudge_at: float | None = None

                while not self._cancelled:
                    now = time.monotonic()

                    if now - started_at >= max_wait_seconds:
                        self._log(
                            (
                                "Достигнут общий тайм-аут Stories: "
                                f"{max_wait_seconds:.0f} секунд"
                            ),
                            on_log,
                        )
                        break

                    page.wait_for_timeout(1000)

                    current_count = len(story_order)

                    if current_count > last_count:
                        last_count = current_count
                        last_growth_at = time.monotonic()
                        last_nudge_at = None

                    silent_for = (
                        time.monotonic()
                        - last_growth_at
                    )

                    if silent_for < stall_threshold:
                        continue

                    can_nudge = (
                        nudges_done < max_nudges
                        and (
                            last_nudge_at is None
                            or (
                                time.monotonic()
                                - last_nudge_at
                                >= stall_threshold
                            )
                        )
                    )

                    if can_nudge:
                        self._nudge(
                            page,
                            on_log,
                        )

                        nudges_done += 1
                        last_nudge_at = time.monotonic()
                        continue

                    if last_nudge_at is None:
                        self._log(
                            "Stories больше не переключаются",
                            on_log,
                        )
                        break

                    after_last_nudge = (
                        time.monotonic()
                        - last_nudge_at
                    )

                    if (
                        after_last_nudge
                        >= final_stall_after_nudge
                    ):
                        self._log(
                            (
                                "Новых Stories больше не появляется — "
                                "сбор завершён"
                            ),
                            on_log,
                        )
                        break

                if self._cancelled:
                    self._log(
                        "Сбор Stories отменён",
                        on_log,
                    )

        finally:
            self._browser = None

            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass

        result = [
            story_registry[key]
            for key in story_order
            if key in story_registry
        ]

        self._log(
            f"Stories найдено всего: {len(result)}",
            on_log,
        )

        return result

    def download(
        self,
        urls: list[str],
        folder: Path | str,
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
                    "Скачивание Stories отменено",
                    on_log,
                )
                break

            path = folder / f"story_{index:03}.jpg"

            if (
                skip_existing
                and path.exists()
                and path.stat().st_size > 0
            ):
                skipped += 1

                self._log(
                    f"Stories {index}/{total}: уже существует",
                    on_log,
                )
                continue

            try:
                response = session.get(
                    url,
                    timeout=30,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                    },
                )
                response.raise_for_status()

                path.write_bytes(response.content)
                saved += 1

                self._log(
                    f"Stories скачано: {index}/{total}",
                    on_log,
                )

            except Exception as exc:
                self._log(
                    f"Ошибка скачивания Stories {index}: {exc}",
                    on_log,
                )

        self._log(
            (
                f"Stories сохранено: {saved}; "
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
