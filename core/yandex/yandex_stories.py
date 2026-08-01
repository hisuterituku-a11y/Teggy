from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Callable

import requests
from playwright.sync_api import Browser, Page, sync_playwright


LogCallback = Callable[[str], None]


class YandexStoriesDownloader:
    """Собирает изображения Stories организации Яндекс Карт."""

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, headless: bool = True, timeout: int = 30) -> None:
        self.headless = headless
        self.timeout = timeout
        self._cancelled = False
        self._browser: Browser | None = None

    def _log(self, text: str, on_log: LogCallback | None = None) -> None:
        if on_log:
            on_log(text)
        else:
            print(f"[Stories] {text}")

    @staticmethod
    def _story_key(url: str) -> str:
        clean_url = url.split("?", 1)[0]
        if clean_url.endswith("/orig"):
            return clean_url[:-5]
        parts = clean_url.rsplit("/", 1)
        if len(parts) == 2 and re.fullmatch(r"\d+x\d+", parts[1]):
            return parts[0]
        return clean_url

    @staticmethod
    def _is_story_image(url: str) -> bool:
        clean_url = url.split("?", 1)[0]
        if "get-maps_stories" not in clean_url:
            return False
        last = clean_url.rsplit("/", 1)[-1]
        return last == "orig" or bool(re.fullmatch(r"\d+x\d+", last))

    @staticmethod
    def _carousel_state(page: Page) -> tuple[str, ...]:
        try:
            result = page.evaluate(
                """
                () => [...document.querySelectorAll('.story-cover-preview')]
                    .map((el) => {
                        const inner = el.querySelector('.story-cover-preview__inner');
                        const img = el.querySelector('img');
                        return (inner ? getComputedStyle(inner).backgroundImage : '') ||
                               (img ? (img.currentSrc || img.src || '') : '') ||
                               el.outerHTML.slice(0, 300);
                    })
                """
            )
            return tuple(str(item) for item in result)
        except Exception:
            return ()

    def _click_carousel_arrow(self, page: Page, direction: str) -> bool:
        side = "_next" if direction == "next" else "_prev"
        selectors = (
            ".business-stories-view__carousel "
            f".carousel__arrow-wrapper.{side} .carousel__arrow",
            f".carousel__arrow-wrapper.{side} .carousel__arrow",
        )
        for selector in selectors:
            try:
                arrow = page.locator(selector).first
                if arrow.count() == 0 or not arrow.is_visible():
                    continue
                before = self._carousel_state(page)
                arrow.click(force=True, timeout=3000)
                for _ in range(20):
                    page.wait_for_timeout(100)
                    after = self._carousel_state(page)
                    if after and after != before:
                        return True
            except Exception:
                continue
        return False

    def _preload_story_covers(
        self,
        page: Page,
        on_log: LogCallback | None,
        max_steps: int = 60,
    ) -> None:
        self._log("Пролистываем ленту обложек Stories до конца", on_log)
        steps = 0
        while (
            not self._cancelled
            and steps < max_steps
            and self._click_carousel_arrow(page, "next")
        ):
            steps += 1
            page.wait_for_timeout(250)

        self._log(f"Лента Stories пройдена: {steps} шагов вправо", on_log)
        self._log("Возвращаем ленту Stories в начало", on_log)

        back_steps = 0
        while (
            not self._cancelled
            and back_steps < max_steps
            and self._click_carousel_arrow(page, "prev")
        ):
            back_steps += 1
            page.wait_for_timeout(200)

        self._log(f"Лента Stories возвращена: {back_steps} шагов влево", on_log)

    @staticmethod
    def _viewer_open(page: Page) -> bool:
        selectors = (
            ".story-screen-view",
            "[class*='story-screen']",
            "[class*='stories-player']",
        )
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() and locator.is_visible():
                    return True
            except Exception:
                continue
        return False

    def _open_first_story(self, page: Page) -> bool:
        try:
            cards = page.locator(".story-cover-preview")
            if cards.count() == 0:
                return False
            card = cards.first
            card.scroll_into_view_if_needed(timeout=3000)
            card.click(force=True, timeout=5000)
            page.wait_for_timeout(1000)
            return self._viewer_open(page)
        except Exception:
            return False

    def _nudge_viewer(self, page: Page, on_log: LogCallback | None) -> bool:
        selectors = (
            ".story-screen-view__next",
            "[aria-label='Следующая история']",
            "[aria-label='Next story']",
            "[class*='story'] [class*='next']",
        )

        for selector in selectors:
            try:
                button = page.locator(selector).first
                if button.count() and button.is_visible():
                    button.click(force=True, timeout=1500)
                    self._log("Stories подвисли: нажимаем Далее один раз", on_log)
                    return True
            except Exception:
                continue

        try:
            page.keyboard.press("ArrowRight")
            self._log("Stories подвисли: нажимаем стрелку вправо один раз", on_log)
            return True
        except Exception:
            self._log("Stories подвисли, но переключить их не удалось", on_log)
            return False

    def collect(
        self,
        url: str,
        on_log: LogCallback | None = None,
        max_wait_seconds: float = 900.0,
        stall_seconds: float = 14.0,
        max_stall_nudges: int = 5,
        finish_after_last_nudge: float = 20.0,
    ) -> list[str]:
        self._cancelled = False
        registry: dict[str, str] = {}
        order: list[str] = []
        browser: Browser | None = None

        def add_url(image_url: str) -> None:
            if not self._is_story_image(image_url):
                return
            clean_url = image_url.split("?", 1)[0]
            key = self._story_key(clean_url)
            current = registry.get(key)
            if current is None:
                order.append(key)
                registry[key] = clean_url
                self._log(f"Stories найдено: {len(order)}", on_log)
            elif clean_url.endswith("/orig") and not current.endswith("/orig"):
                registry[key] = clean_url

        try:
            with sync_playwright() as playwright:
                self._log("Открываем Яндекс Карты для сбора Stories", on_log)
                browser = playwright.chromium.launch(headless=self.headless)
                self._browser = browser
                context = browser.new_context(
                    viewport={"width": 1400, "height": 900},
                    user_agent=self.USER_AGENT,
                    locale="ru-RU",
                )
                page = context.new_page()
                page.on("response", lambda response: add_url(response.url))
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout * 1000,
                )
                page.wait_for_timeout(5000)

                if self._cancelled:
                    return []

                self._preload_story_covers(page, on_log)
                cards_count = page.locator(".story-cover-preview").count()
                self._log(f"Карточек Stories в DOM: {cards_count}", on_log)

                if cards_count == 0:
                    self._log("Stories у организации не найдены", on_log)
                    return []

                if not self._open_first_story(page):
                    self._log("Не удалось открыть первую Stories", on_log)
                    return []

                self._log(
                    "Первая Stories открыта. Ждём автоматического показа всех Stories без кликов",
                    on_log,
                )

                started_at = time.monotonic()
                last_growth_at = started_at
                last_count = len(order)
                nudges = 0
                last_nudge_at: float | None = None

                while not self._cancelled:
                    now = time.monotonic()

                    if now - started_at >= max_wait_seconds:
                        self._log(
                            f"Достигнут общий тайм-аут Stories: {max_wait_seconds:.0f} секунд",
                            on_log,
                        )
                        break

                    page.wait_for_timeout(1000)
                    current_count = len(order)

                    if current_count > last_count:
                        last_count = current_count
                        last_growth_at = time.monotonic()
                        last_nudge_at = None
                        continue

                    silent_for = time.monotonic() - last_growth_at
                    if silent_for < stall_seconds:
                        continue

                    if nudges < max_stall_nudges:
                        if self._nudge_viewer(page, on_log):
                            nudges += 1
                            last_nudge_at = time.monotonic()
                            last_growth_at = last_nudge_at
                            page.wait_for_timeout(1200)
                            continue

                    if last_nudge_at is None:
                        self._log("Stories перестали переключаться", on_log)
                        break

                    if time.monotonic() - last_nudge_at >= finish_after_last_nudge:
                        self._log(
                            "После последней попытки новые Stories не появились, сбор завершён",
                            on_log,
                        )
                        break

        finally:
            self._browser = None
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass

        result = [registry[key] for key in order if key in registry]
        self._log(f"Stories найдено всего: {len(result)}", on_log)
        return result

    def download(
        self,
        urls: list[str],
        folder: Path | str,
        on_log: LogCallback | None = None,
        skip_existing: bool = True,
    ) -> int:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        session = requests.Session()
        total = len(urls)
        saved = 0
        skipped = 0
        failed = 0

        for index, url in enumerate(urls, start=1):
            if self._cancelled:
                self._log("Скачивание Stories отменено", on_log)
                break

            path = folder / f"story_{index:03}.jpg"
            if skip_existing and path.exists() and path.stat().st_size > 0:
                skipped += 1
                self._log(f"Stories {index}/{total}: уже существует", on_log)
                continue

            try:
                response = session.get(
                    url,
                    timeout=30,
                    headers={
                        "User-Agent": self.USER_AGENT,
                        "Referer": "https://yandex.ru/maps/",
                    },
                )
                response.raise_for_status()
                if not response.content:
                    raise RuntimeError("сервер вернул пустой файл")
                path.write_bytes(response.content)
                saved += 1
                self._log(f"Stories скачано: {index}/{total}", on_log)
            except Exception as exc:
                failed += 1
                path.unlink(missing_ok=True)
                self._log(f"Ошибка скачивания Stories {index}: {exc}", on_log)

        self._log(
            f"Stories сохранено: {saved}; пропущено: {skipped}; ошибок: {failed}",
            on_log,
        )
        return saved

    def cancel(self) -> None:
        self._cancelled = True
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
