from abc import ABC, abstractmethod
from typing import List, Optional
from core.photo_import.models import PhotoInfo, SourceType, ImportStatus
from core.photo_import.exceptions import ParserError, NetworkError, CancelledError


# ===== БАЗОВЫЙ ПАРСЕР =====

class BaseParser(ABC):
    """Базовый парсер для всех источников."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        
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
    """Парсер Яндекс Карт."""

    def __init__(self, timeout: int = 30000):
        super().__init__(timeout)
        self._source_type = SourceType.YANDEX

    def parse(self, url: str) -> List[PhotoInfo]:
        from playwright.sync_api import sync_playwright
        import time

        photo_urls = set()
        self._is_cancelled = False

        def extract(obj):
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
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                self._page = self._browser.new_page()
                self._page.on("response", handle_response)

                self._log(f"Открываем страницу: {url}")

                if "/gallery/" in url or "photos[business]" in url:
                    self._page.goto(url, wait_until='domcontentloaded')
                    self._page.wait_for_timeout(3000)
                else:
                    self._page.goto(url, wait_until='domcontentloaded')
                    self._page.wait_for_timeout(5000)

                    try:
                        self._log("Ищем раздел 'Фото'...")
                        try:
                            foto_btn = self._page.get_by_text("Фото", exact=True).first
                            if foto_btn.count():
                                foto_btn.click()
                                self._log("Нажали 'Фото' по тексту")
                                self._page.wait_for_timeout(3000)
                        except:
                            pass

                        if not foto_btn or not foto_btn.count():
                            try:
                                foto_btn = self._page.locator(
                                    '.tabs-menu__item, [class*="tab"], button:has-text("Фото"), a:has-text("Фото")'
                                ).first
                                if foto_btn.count():
                                    foto_btn.click()
                                    self._log("Нажали 'Фото' по селектору")
                                    self._page.wait_for_timeout(3000)
                            except:
                                pass

                        if not foto_btn or not foto_btn.count():
                            try:
                                gallery_link = self._page.locator('a[href*="/gallery/"]').first
                                if gallery_link.count():
                                    self._page.goto(gallery_link.get_attribute('href'))
                                    self._log("Перешли по ссылке /gallery/")
                                    self._page.wait_for_timeout(3000)
                            except:
                                pass

                    except Exception as e:
                        self._log(f"Не удалось открыть раздел Фото: {e}")

                    if "/gallery/" not in self._page.url:
                        self._log("Пробуем добавить /gallery/ вручную...")
                        base_url = url.split('?')[0]
                        if base_url.endswith('/'):
                            gallery_url = base_url + 'gallery/'
                        else:
                            gallery_url = base_url + '/gallery/'
                        self._page.goto(gallery_url, wait_until='domcontentloaded')
                        self._page.wait_for_timeout(3000)

                try:
                    self._log("Открываем первое фото...")
                    self._page.locator("img").nth(0).click()
                    self._page.wait_for_timeout(2000)
                except:
                    self._log("Не удалось открыть первое фото, пробуем дальше")

                self._log("Начинаем сбор фотографий...")

                previous_count = 0
                stable_count = 0

                for i in range(500):
                    if self._is_cancelled:
                        break

                    self._page.mouse.wheel(0, 5000)

                    try:
                        self._page.keyboard.press("ArrowRight")
                    except:
                        pass

                    time.sleep(0.5)

                    current_count = len(photo_urls)
                    self._log(f"[{i+1}/500] Найдено фотографий: {current_count}")

                    if current_count == previous_count:
                        stable_count += 1
                    else:
                        stable_count = 0

                    previous_count = current_count

                    if stable_count >= 30:
                        self._log("Новых фотографий давно нет. Останавливаемся.")
                        break

                self._log(f"Всего найдено: {len(photo_urls)}")
                self._browser.close()

        except Exception as e:
            if self._is_cancelled:
                raise CancelledError("Парсинг отменён пользователем")
            raise ParserError(f"Ошибка парсинга: {e}")
        finally:
            self._close_browser()

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
        print(f"[YandexParser] {message}")

    def _close_browser(self) -> None:
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