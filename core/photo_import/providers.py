from abc import ABC, abstractmethod
from typing import List, Optional
from core.photo_import.models import PhotoInfo, SourceType, ImportStatus
from core.photo_import.exceptions import ParserError, NetworkError, CancelledError


# ===== БАЗОВЫЙ ПАРСЕР =====

class BaseParser(ABC):
    """Базовый парсер для всех источников."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self._is_cancelled = False
        self._source_type: Optional[SourceType] = None

    @abstractmethod
    def parse(self, url: str) -> List[PhotoInfo]:
        pass

    @abstractmethod
    def supports_url(self, url: str) -> bool:
        pass

    def cancel(self) -> None:
        self._is_cancelled = True

    def close(self) -> None:
        pass

    @property
    def source_type(self) -> Optional[SourceType]:
        return self._source_type


# ===== ПАРСЕРЫ =====


# В core/photo_import/providers.py

class YandexParser(BaseParser):
    """Парсер Яндекс Карт на основе рабочего скрипта."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        super().__init__(headless, timeout)
        self._source_type = SourceType.YANDEX
        self._browser = None
        self._page = None
        self._playwright = None

    def parse(self, url: str, max_photos: int = 100) -> List[PhotoInfo]:
        """
        Парсит фотографии из Яндекс Карт.

        Использует проверенную логику из рабочего скрипта.
        """
        from playwright.sync_api import sync_playwright
        import time

        photo_urls = set()
        self._is_cancelled = False

        def extract(obj):
            """Рекурсивно обходит JSON и ищет ссылки на avatars.mds.yandex.net."""
            if self._is_cancelled:
                return
            if isinstance(obj, dict):
                for value in obj.values():
                    extract(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item)
            elif isinstance(obj, str):
                if "avatars.mds.yandex.net" in obj:
                    clean_url = obj.split("?")[0]
                    photo_urls.add(clean_url)

        def handle_response(response):
            """Обрабатывает ответы страницы."""
            if self._is_cancelled:
                return
            try:
                if "photos" in response.url:
                    try:
                        json_data = response.json()
                        extract(json_data)
                    except:
                        pass
            except:
                pass
            try:
                url = response.url
                if "avatars.mds.yandex.net" in url:
                    clean_url = url.split("?")[0]
                    photo_urls.add(clean_url)
            except:
                pass

        try:
            with sync_playwright() as p:
                self._playwright = p
                self._browser = p.chromium.launch(
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )
                self._page = self._browser.new_page()

                # Ловим все ответы
                self._page.on("response", handle_response)

                self._log("Открываем карточку...")
                self._page.goto(url, wait_until='domcontentloaded')
                self._page.wait_for_timeout(5000)

                # Открываем раздел Фото
                try:
                    self._log("Открываем раздел Фото...")
                    self._page.get_by_text("Фото").click()
                    self._page.wait_for_timeout(3000)
                except:
                    self._log("Не удалось открыть вкладку Фото.")

                # Открываем первое фото
                try:
                    self._page.locator("img").nth(0).click()
                    self._page.wait_for_timeout(2000)
                except:
                    pass

                self._log("Начинаем прокрутку...")

                previous_count = 0
                stable_count = 0

                # До 500 итераций (как в рабочем скрипте)
                for i in range(500):
                    if self._is_cancelled:
                        break

                    # Листаем вниз
                    self._page.mouse.wheel(0, 5000)

                    # Переключаем фото
                    try:
                        self._page.keyboard.press("ArrowRight")
                    except:
                        pass

                    time.sleep(0.5)

                    current_count = len(photo_urls)

                    self._log(f"[{i+1}/500] Найдено фотографий: {current_count}")

                    # Если число фотографий перестало расти
                    if current_count == previous_count:
                        stable_count += 1
                    else:
                        stable_count = 0

                    previous_count = current_count

                    # Если 30 итераций подряд ничего нового
                    if stable_count >= 30:
                        self._log("Новых фотографий давно нет. Останавливаемся.")
                        break

                    # Если достигли лимита
                    if len(photo_urls) >= max_photos:
                        self._log(f"Достигнут лимит: {max_photos}")
                        break

                self._log(f"Всего найдено: {len(photo_urls)}")
                self._browser.close()

        except Exception as e:
            if self._is_cancelled:
                raise CancelledError("Парсинг отменён пользователем")
            raise ParserError(f"Ошибка парсинга: {e}")
        finally:
            self._close_browser()

        # Возвращаем список PhotoInfo
        return [
            PhotoInfo(
                url=url,
                filename=f"{i+1}.jpg",
                source=self._source_type,
                status=ImportStatus.PENDING
            )
            for i, url in enumerate(photo_urls)
        ]

    def _log(self, message: str) -> None:
        """Внутреннее логирование."""
        print(f"[YandexParser] {message}")

    def _close_browser(self) -> None:
        """Закрывает браузер."""
        if self._page:
            try:
                self._page.close()
            except:
                pass
            self._page = None
        if self._browser:
            try:
                self._browser.close()
            except:
                pass
            self._browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except:
                pass
            self._playwright = None

    def cancel(self) -> None:
        self._is_cancelled = True

    def close(self) -> None:
        self._close_browser()

    def supports_url(self, url: str) -> bool:
        return "yandex.ru/maps" in url or "yandex.by/maps" in url

class GoogleParser(BaseParser):
    """Парсер Google Maps (заглушка)."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        super().__init__(headless, timeout)
        self._source_type = SourceType.GOOGLE

    def parse(self, url: str) -> List[PhotoInfo]:
        # TODO: Реализовать парсинг Google Maps
        return []

    def supports_url(self, url: str) -> bool:
        return "google.com/maps" in url


class TwoGISParser(BaseParser):
    """Парсер 2GIS (заглушка)."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        super().__init__(headless, timeout)
        self._source_type = SourceType.TWOGIS

    def parse(self, url: str) -> List[PhotoInfo]:
        # TODO: Реализовать парсинг 2GIS
        return []

    def supports_url(self, url: str) -> bool:
        return "2gis.ru" in url