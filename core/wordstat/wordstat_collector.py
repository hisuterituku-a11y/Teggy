from __future__ import annotations

import csv
import io
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode

from playwright.sync_api import (
    BrowserContext,
    Download,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


LogCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class WordstatQuery:
    """Один запрос из Яндекс Вордстата."""

    phrase: str
    frequency: int
    query_type: str = "included"


class WordstatCollector:
    """
    Сборщик запросов из Яндекс Вордстата.

    Использует постоянный профиль Chromium, поэтому пользователь
    авторизуется в Яндексе один раз, а сессия сохраняется между запусками.
    """

    WORDSTAT_URL = "https://wordstat.yandex.ru/"

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 90,
        profile_dir: Path | str | None = None,
    ) -> None:
        self.headless = headless
        self.timeout = timeout

        if profile_dir is None:
            profile_dir = (
                Path.home()
                / ".teggy"
                / "browser"
                / "yandex_wordstat"
            )

        self.profile_dir = Path(profile_dir)

        self._cancelled = False
        self._context: BrowserContext | None = None

    def _log(
        self,
        text: str,
        on_log: LogCallback | None = None,
    ) -> None:
        if on_log:
            on_log(text)
        else:
            print(f"[Wordstat] {text}")

    def _check_cancelled(self) -> None:
        if self._cancelled:
            raise WordstatCancelledError(
                "Сбор запросов отменён пользователем"
            )

    @staticmethod
    def _normalize_phrase(value: str) -> str:
        return " ".join(value.split()).strip()

    @staticmethod
    def _parse_frequency(value: str) -> int:
        """
        Преобразует варианты вроде:
        12 345
        12 345
        12,345
        в целое число.
        """

        digits = re.sub(r"[^\d]", "", value)

        if not digits:
            return 0

        return int(digits)

    @staticmethod
    def _build_url(
        query: str,
        region: str = "all",
    ) -> str:
        params = urlencode(
            {
                "region": region,
                "view": "table",
                "words": query,
            }
        )

        return f"{WordstatCollector.WORDSTAT_URL}?{params}"

    def _wait_for_authorization(
        self,
        page: Page,
        on_log: LogCallback | None,
    ) -> None:
        """
        Если Wordstat отправил пользователя на авторизацию,
        оставляет браузер открытым и ждёт ручного входа.
        """

        login_markers = (
            "passport.yandex",
            "auth.yandex",
        )

        if not any(marker in page.url for marker in login_markers):
            return

        if self.headless:
            raise WordstatAuthorizationError(
                "Яндекс требует авторизацию. "
                "Запустите сборщик с headless=False и войдите в аккаунт."
            )

        self._log(
            "Требуется вход в Яндекс. Авторизуйтесь в открытом браузере.",
            on_log,
        )

        deadline = time.monotonic() + 300

        while time.monotonic() < deadline:
            self._check_cancelled()

            if not any(
                marker in page.url
                for marker in login_markers
            ):
                self._log(
                    "Авторизация успешно завершена",
                    on_log,
                )
                return

            page.wait_for_timeout(1000)

        raise WordstatAuthorizationError(
            "Не удалось дождаться авторизации в Яндексе"
        )

    def _wait_for_results(
        self,
        page: Page,
        on_log: LogCallback | None,
    ) -> None:
        self._log(
            "Ожидаем результаты Вордстата",
            on_log,
        )

        selectors = (
            "table",
            '[role="table"]',
            '[role="row"]',
            "text=Топы запросов",
            "text=Популярные запросы",
        )

        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            self._check_cancelled()

            for selector in selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.wait_for_timeout(1500)
                        return
                except Exception:
                    continue

            page.wait_for_timeout(500)

        raise WordstatError(
            "Wordstat не показал результаты за отведённое время"
        )

    def _open_top_queries(
        self,
        page: Page,
        on_log: LogCallback | None,
    ) -> None:
        """
        Пытается открыть вкладку с топами запросов.

        Названия и разметка могут меняться, поэтому используются
        несколько вариантов поиска элемента.
        """

        candidates = (
            page.get_by_text(
                "Топы запросов",
                exact=True,
            ),
            page.get_by_text(
                "Топ запросов",
                exact=True,
            ),
            page.get_by_role(
                "tab",
                name=re.compile(
                    r"Топы?\s+запросов",
                    re.IGNORECASE,
                ),
            ),
        )

        for locator in candidates:
            try:
                if locator.count() < 1:
                    continue

                locator.first.click(timeout=5000)

                page.wait_for_timeout(1000)

                try:
                    page.locator(
                        "table, [role='table'], [role='row']"
                    ).first.wait_for(
                        state="visible",
                        timeout=10_000,
                    )
                except Exception:
                    pass

                self._log(
                    "Открыта вкладка «Топы запросов»",
                    on_log,
                )
                return

            except Exception:
                continue

        self._log(
            "Вкладка «Топы запросов» явно не найдена, "
            "читаем текущую таблицу",
            on_log,
        )

    @staticmethod
    def _find_download_button(
        page: Page,
    ) -> Locator | None:
        candidates = (
            page.get_by_role(
                "button",
                name=re.compile(
                    r"Скачать",
                    re.IGNORECASE,
                ),
            ),
            page.get_by_role(
                "link",
                name=re.compile(
                    r"Скачать",
                    re.IGNORECASE,
                ),
            ),
            page.get_by_text(
                "Скачать",
                exact=True,
            ),
        )

        for locator in candidates:
            try:
                if locator.count() > 0:
                    return locator.first
            except Exception:
                continue

        return None

    def _download_csv(
        self,
        page: Page,
        on_log: LogCallback | None,
    ) -> bytes | None:
        button = self._find_download_button(page)

        if button is None:
            self._log(
                "Кнопка «Скачать» не найдена",
                on_log,
            )
            return None

        try:
            self._log(
                "Открываем меню выгрузки",
                on_log,
            )

            button.click(timeout=10_000)
            page.wait_for_timeout(700)

            # Стабильнее искать ссылку с атрибутом download, а не текст меню.
            csv_link = page.locator(
                'a[download="wordstat_top_queries"]'
            ).first

            if csv_link.count() < 1 or not csv_link.is_visible():
                # Резервный вариант на случай изменения имени download.
                csv_link = page.locator(
                    "a[download] button.save-csv-button"
                ).first

            if csv_link.count() < 1 or not csv_link.is_visible():
                self._log(
                    "Пункт CSV в меню выгрузки не найден",
                    on_log,
                )

                page.screenshot(
                    path="wordstat_download_menu.png",
                    full_page=True,
                )
                return None

            self._log(
                "Выбираем формат CSV",
                on_log,
            )

            with page.expect_download(timeout=30_000) as download_info:
                csv_link.click(timeout=10_000)

            download: Download = download_info.value
            save_path = Path.cwd() / download.suggested_filename

            download.save_as(str(save_path))
            content = save_path.read_bytes()

            self._log(
                f"CSV сохранён: {save_path}",
                on_log,
            )
            self._log(
                f"Получен файл: {download.suggested_filename}",
                on_log,
            )

            if not content:
                self._log(
                    "Полученный CSV-файл оказался пустым",
                    on_log,
                )
                return None

            self._log(
                f"CSV-выгрузка получена: {len(content)} байт",
                on_log,
            )

            return content

        except PlaywrightTimeoutError:
            self._log(
                "Не удалось дождаться CSV-выгрузки",
                on_log,
            )

            try:
                page.screenshot(
                    path="wordstat_download_timeout.png",
                    full_page=True,
                )
            except Exception:
                pass

            return None

        except Exception as exc:
            self._log(
                f"Ошибка CSV-выгрузки: {exc}",
                on_log,
            )

            try:
                page.screenshot(
                    path="wordstat_download_error.png",
                    full_page=True,
                )
            except Exception:
                pass

            return None

    @staticmethod
    def _decode_csv(content: bytes) -> str:
        encodings = (
            "utf-8-sig",
            "utf-8",
            "windows-1251",
        )

        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue

        return content.decode(
            "utf-8",
            errors="replace",
        )

    def _parse_csv(
        self,
        content: bytes,
        on_log: LogCallback | None,
    ) -> list[WordstatQuery]:
        """
        Разбирает CSV, который отдаёт Яндекс Вордстат.

        Файл приходит в UTF-8 с BOM и использует точку с запятой
        как разделитель. splitlines() дополнительно защищает от
        нестандартных переводов строк в выгрузке.
        """

        text = self._decode_csv(content)
        reader = csv.reader(
            text.splitlines(),
            delimiter=";",
        )

        results: list[WordstatQuery] = []

        for row_number, row in enumerate(reader):
            if len(row) < 2:
                continue

            phrase = self._normalize_phrase(row[0])
            frequency = self._parse_frequency(row[1])

            # Первая строка является заголовком.
            if row_number == 0:
                continue

            if not phrase or frequency <= 0:
                continue

            results.append(
                WordstatQuery(
                    phrase=phrase,
                    frequency=frequency,
                )
            )

        results = self._deduplicate(results)

        self._log(
            f"Из CSV прочитано запросов: {len(results)}",
            on_log,
        )

        return results

    def _parse_dom(
        self,
        page: Page,
        on_log: LogCallback | None,
    ) -> list[WordstatQuery]:
        """
        Резервный разбор видимых строк.

        Не привязан к случайным CSS-классам Яндекса:
        ищет строки таблиц и извлекает из текста фразу с числом.
        """

        self._log(
            "Пробуем прочитать таблицу со страницы",
            on_log,
        )

        raw_rows: list[str] = []

        row_selectors = (
            "table tbody tr",
            '[role="table"] [role="row"]',
            '[role="row"]',
        )

        for selector in row_selectors:
            try:
                locator = page.locator(selector)

                for index in range(locator.count()):
                    self._check_cancelled()

                    text = locator.nth(index).inner_text().strip()

                    if text:
                        raw_rows.append(text)

                if raw_rows:
                    break

            except Exception:
                continue

        results: list[WordstatQuery] = []

        for raw_text in raw_rows:
            lines = [
                self._normalize_phrase(line)
                for line in raw_text.splitlines()
                if self._normalize_phrase(line)
            ]

            if len(lines) < 2:
                continue

            frequency_index: int | None = None
            frequency = 0

            for index in range(len(lines) - 1, -1, -1):
                candidate = lines[index]

                if not re.fullmatch(
                    r"[\d\s\u00a0.,]+",
                    candidate,
                ):
                    continue

                parsed = self._parse_frequency(candidate)

                if parsed > 0:
                    frequency_index = index
                    frequency = parsed
                    break

            if frequency_index is None:
                continue

            phrase_candidates = [
                line
                for index, line in enumerate(lines)
                if index != frequency_index
                and not re.fullmatch(
                    r"[\d\s\u00a0.,%]+",
                    line,
                )
            ]

            if not phrase_candidates:
                continue

            phrase = max(
                phrase_candidates,
                key=len,
            )

            lowered = phrase.casefold()

            if any(
                ignored in lowered
                for ignored in (
                    "популярные запросы",
                    "похожие запросы",
                    "число запросов",
                    "частотность",
                )
            ):
                continue

            results.append(
                WordstatQuery(
                    phrase=phrase,
                    frequency=frequency,
                )
            )

        self._log(
            f"Со страницы прочитано запросов: {len(results)}",
            on_log,
        )

        return self._deduplicate(results)

    @staticmethod
    def _deduplicate(
        values: list[WordstatQuery],
    ) -> list[WordstatQuery]:
        unique: dict[str, WordstatQuery] = {}

        for item in values:
            key = item.phrase.casefold()

            existing = unique.get(key)

            if (
                existing is None
                or item.frequency > existing.frequency
            ):
                unique[key] = item

        return sorted(
            unique.values(),
            key=lambda item: item.frequency,
            reverse=True,
        )

    def collect(
        self,
        query: str,
        region: str = "all",
        on_log: LogCallback | None = None,
    ) -> list[WordstatQuery]:
        self._cancelled = False

        query = self._normalize_phrase(query)

        if not query:
            raise ValueError(
                "Не указан ключевой запрос"
            )

        self.profile_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        target_url = self._build_url(
            query=query,
            region=region,
        )

        self._log(
            f"Начинаем сбор по запросу: {query}",
            on_log,
        )

        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.profile_dir),
                    headless=self.headless,
                    viewport={
                        "width": 1920,
                        "height": 1080,
                    },
                    accept_downloads=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                    ],
                )

                self._context = context

                page = (
                    context.pages[0]
                    if context.pages
                    else context.new_page()
                )

                self._log(
                    f"Открываем Wordstat: {target_url}",
                    on_log,
                )

                page.goto(
                    target_url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout * 1000,
                )

                self._wait_for_authorization(
                    page,
                    on_log,
                )

                if "wordstat.yandex" not in page.url:
                    page.goto(
                        target_url,
                        wait_until="domcontentloaded",
                        timeout=self.timeout * 1000,
                    )

                self._wait_for_results(
                    page,
                    on_log,
                )

                self._open_top_queries(
                    page,
                    on_log,
                )
                page.screenshot(path="wordstat.png", full_page=True)

                with open("wordstat.html", "w", encoding="utf-8") as f:
                    f.write(page.content())

                self._log("HTML сохранён", on_log)
                self._check_cancelled()

                csv_content = self._download_csv(
                    page,
                    on_log,
                )

                if csv_content:
                    results = self._parse_csv(
                        csv_content,
                        on_log,
                    )

                    if results:
                        return results

                results = self._parse_dom(
                    page,
                    on_log,
                )

                if not results:
                    raise WordstatError(
                        "Wordstat открылся, но запросы распознать "
                        "не удалось. Возможно, Яндекс изменил интерфейс."
                    )

                return results

        finally:
            context = self._context
            self._context = None

            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass

    def cancel(self) -> None:
        self._cancelled = True

        context = self._context

        if context is not None:
            try:
                context.close()
            except Exception:
                pass


class WordstatError(RuntimeError):
    """Базовая ошибка сборщика Wordstat."""


class WordstatAuthorizationError(WordstatError):
    """Не удалось пройти авторизацию."""


class WordstatCancelledError(WordstatError):
    """Операция отменена пользователем."""