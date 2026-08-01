from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import requests
from playwright.sync_api import Browser, Page, sync_playwright


LogCallback = Callable[[str], None]


class YandexStoriesDownloader:
    """Собирает изображения из всех карточек Stories организации Яндекс Карт."""

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
            page.wait_for_timeout(200)
        self._log(f"Лента Stories пройдена: {steps} шагов вправо", on_log)

        while not self._cancelled and self._click_carousel_arrow(page, "prev"):
            page.wait_for_timeout(150)

    @staticmethod
    def _viewer_signature(page: Page) -> str:
        try:
            return str(
                page.evaluate(
                    """
                    () => {
                        const nodes = [...document.querySelectorAll(
                            '.story-screen-view img, .story-screen-view [style*="background-image"], '
                            '[class*="story"] img, [class*="story"] [style*="background-image"]'
                        )].filter((el) => {
                            const r = el.getBoundingClientRect();
                            const s = getComputedStyle(el);
                            return r.width > 150 && r.height > 150 &&
                                   s.display !== 'none' && s.visibility !== 'hidden';
                        });
                        const el = nodes.sort((a, b) => {
                            const ar = a.getBoundingClientRect();
                            const br = b.getBoundingClientRect();
                            return br.width * br.height - ar.width * ar.height;
                        })[0];
                        if (!el) return location.href;
                        return [
                            el.currentSrc || '', el.src || '',
                            getComputedStyle(el).backgroundImage || '',
                            el.getAttribute('data-id') || '',
                            el.outerHTML.slice(0, 300)
                        ].join('|');
                    }
                    """
                )
            )
        except Exception:
            return page.url

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

    def _next_story(self, page: Page) -> bool:
        selectors = (
            ".story-screen-view__next",
            "[aria-label='Следующая история']",
            "[aria-label='Next story']",
            "[class*='story'] [class*='next']",
        )
        before = self._viewer_signature(page)

        for selector in selectors:
            try:
                button = page.locator(selector).first
                if button.count() and button.is_visible():
                    button.click(force=True, timeout=1500)
                    break
            except Exception:
                continue
        else:
            try:
                page.keyboard.press("ArrowRight")
            except Exception:
                return False

        for _ in range(15):
            page.wait_for_timeout(120)
            if not self._viewer_open(page):
                return False
            if self._viewer_signature(page) != before:
                return True
        return False

    @staticmethod
    def _close_viewer(page: Page) -> None:
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(350)
        except Exception:
            pass

    def _open_card(self, page: Page, index: int) -> bool:
        self._close_viewer(page)
        cards = page.locator(".story-cover-preview")
        if index >= cards.count():
            return False
        try:
            card = cards.nth(index)
            card.scroll_into_view_if_needed(timeout=3000)
            card.click(force=True, timeout=5000)
            page.wait_for_timeout(800)
            return self._viewer_open(page)
        except Exception:
            return False

    def collect(
        self,
        url: str,
        on_log: LogCallback | None = None,
        max_slides_per_card: int = 50,
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

                for card_index in range(cards_count):
                    if self._cancelled:
                        break

                    before_card = len(order)
                    self._log(
                        f"Открываем карточку Stories {card_index + 1}/{cards_count}",
                        on_log,
                    )
                    if not self._open_card(page, card_index):
                        self._log(
                            f"Карточку Stories {card_index + 1} открыть не удалось",
                            on_log,
                        )
                        continue

                    page.wait_for_timeout(700)
                    seen_signatures: set[str] = set()
                    unchanged = 0

                    for _ in range(max_slides_per_card):
                        if self._cancelled or not self._viewer_open(page):
                            break

                        signature = self._viewer_signature(page)
                        if signature in seen_signatures:
                            unchanged += 1
                        else:
                            seen_signatures.add(signature)
                            unchanged = 0

                        count_before = len(order)
                        page.wait_for_timeout(450)
                        if len(order) == count_before:
                            unchanged += 1
                        else:
                            unchanged = 0

                        if unchanged >= 3 or not self._next_story(page):
                            break

                    self._close_viewer(page)
                    found_in_card = len(order) - before_card
                    self._log(
                        f"Карточка {card_index + 1}/{cards_count}: "
                        f"найдено новых Stories: {found_in_card}; всего: {len(order)}",
                        on_log,
                    )

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
