from abc import ABC, abstractmethod
from typing import List, Optional
from core.photo_import.models import PhotoInfo, SourceType, ImportStatus
from core.photo_import.exceptions import ParserError, NetworkError, CancelledError
from core.paths import resource_path
import json
import time
from pathlib import Path

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
    """Парсер Яндекс Карт."""

    # мусорные ссылки Яндекса, которые не сохраняем
    BAD_URL_PARTS = [
        "{size}",
        "%7Bsize%7D",
        "%s",
        "get-yapic",     # аватарки пользователей
        "get-tycoon",    # витрина
        "get-direct",    # служебные
        "get-bunker",    # служебные
               # временно: превью видео, видео пока не собираем
    ]

    # временно: показывать служебную статистику (pool_stats/video/stories)
    # в логах. Для релизной сборки — False, пользователь это видеть не должен.
    DEBUG = False

    # размеры Яндекса от худшего к лучшему качеству
    QUALITY_RANK = {
        "S": 1,
        "M": 2,
        "L": 3,
        "XL": 4,
        "XXL": 5,
        "XXXL": 6,
    }

    def __init__(self, headless: bool = False, timeout: int = 30000):
        # ВРЕМЕННО: дефолт headless=True незаметно "терял" видимое окно,
        # если parser создавался без явного headless=False где-то в UI/
        # конфиге — искать все места создания сейчас некогда, поэтому
        # на время разработки дефолт принудительно False.
        # ИСПРАВЛЕНО: раньше было super().__init__(timeout), из-за чего
        # timeout попадал в параметр headless, а self.timeout всегда
        # оставался равен дефолтному значению 30000.
        super().__init__(headless=headless, timeout=timeout)
        self._source_type = SourceType.YANDEX

        self.passport = {}

        # нормализованный ключ -> лучший URL (максимальное качество)
        self.photo_registry = {}

        # нормализованный ключ -> категория ("organization" / "reviews")
        self.photo_categories = {}

        # порядок обнаружения фото (по ключу), нужен для стабильной
        # нумерации файлов между запусками
        self._photo_order = []
        self._photo_order_set = set()

        # фото организации / отзывов — сырые URL, используются только
        # как счётчик прогресса для _scroll_and_collect
        self.organization_photos = set()
        self.review_photos = set()
        self._phase_activity = {
            "organization": 0,
            "reviews": 0
        }
        # мусор, который нашли, но не сохраняем
        self.ignored_photos = set()

        # сколько раз _register_photo вызывался всего (до дедупа) —
        # нужно только для статистики "Дубли: N" в конце
        self._raw_registered_count = 0

        # ==========================
        # Статистика по пулам Яндекса — только наблюдение, ни на что
        # не влияет и ничего не фильтрует (get-vh, get-maps_stories
        # намеренно НЕ добавлены в BAD_URL_PARTS).
        # ==========================
        self.pool_stats = {}
        self.video_previews = set()   # pool == get-vh (подтверждено: превью видео)
        self.story_previews = set()   # pool == get-maps_stories

        # ИСПРАВЛЕНО: атрибут раньше не инициализировался в __init__.
        # Обработчик handle_response подключается сразу после создания
        # страницы и мог обратиться к self.current_photo_source ещё до
        # того, как он выставлялся в parse() (AttributeError глушился
        # общим except Exception: pass, и фото на этом этапе терялись).
        self.current_photo_source = None

        self._playwright = None
        self._browser = None
        self._page = None

    def parse(self, url: str) -> List[PhotoInfo]:

        from playwright.sync_api import sync_playwright
        import os

        # ИСПРАВЛЕНО: раньше PLAYWRIGHT_BROWSERS_PATH безусловно
        # перезаписывался на resource_path("ms-playwright"), даже если
        # такой папки нет (например при запуске из исходников, когда
        # Chromium стоит в обычном кеше после `playwright install
        # chromium`, а не в бандле PyInstaller). В этом случае Playwright
        # искал браузер по несуществующему пути и не мог запуститься.
        # Теперь трогаем переменную только если папка реально есть —
        # иначе оставляем то, что уже было в окружении (стандартный кеш).
        bundled_browsers_path = Path(resource_path("ms-playwright"))
        bundled_browsers_exist = bundled_browsers_path.exists()

        self._log(f"headless={self.headless}, timeout={self.timeout}")
        self._log(f"Playwright bundled path: {bundled_browsers_path}")
        self._log(f"Exists: {bundled_browsers_exist}")

        if bundled_browsers_exist:
            try:
                self._log(
                    f"Содержимое: {[p.name for p in bundled_browsers_path.iterdir()]}"
                )
            except Exception as e:
                self._log(f"Не удалось прочитать содержимое папки: {e}")

            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bundled_browsers_path)
        else:
            self._log(
                "Бандл-папка Playwright не найдена, используем "
                f"PLAYWRIGHT_BROWSERS_PATH из окружения как есть: "
                f"{os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '(не задан)')}"
            )

        self._is_cancelled = False

        # сбрасываем состояние на случай повторного вызова parse()
        self.photo_registry = {}
        self.photo_categories = {}
        self._photo_order = []
        self._photo_order_set = set()
        self.organization_photos = set()
        self.review_photos = set()
        self.ignored_photos = set()
        self._raw_registered_count = 0
        self.pool_stats = {}
        self.video_previews = set()
        self.story_previews = set()
        self.current_photo_source = None

        def handle_response(response):
            if self._is_cancelled:
                return

            try:
                resp_url = response.url

                if "avatars.mds.yandex.net" not in resp_url:
                    return

                clean_url = resp_url.split("?")[0]

                if not self.current_photo_source:
                    return


                # любое получение картинки от Яндекса = активность
                self._phase_activity[self.current_photo_source] += 1


                pool = self._get_pool(clean_url)


                # видео-превью пока не сохраняем
                if pool == "get-vh":
                    self.video_previews.add(clean_url)
                    return


                # сторис пока тоже не сохраняем
                if pool == "get-maps_stories":
                    self.story_previews.add(clean_url)
                    return


                # настоящий мусор
                if any(bad in clean_url for bad in self.BAD_URL_PARTS):
                    self.ignored_photos.add(clean_url)
                    
                    return


                # обычное фото
                self._register_photo(clean_url, self.current_photo_source)

                # ИСПРАВЛЕНО: до открытия /gallery/ или /reviews/ Яндекс
                # успевает прислать логотипы, превью, рекомендации и
                # прочий интерфейсный мусор — эти ответы раньше всё
                # равно попадали в photo_registry без категории и
                # раздували "Всего найдено" сверх суммы
                # organization + reviews. До явного входа в одну из
                # фаз такие фото вообще не регистрируем.
                if not self.current_photo_source:
                    return

                # ==========================
                # Статистика по пулам — только наблюдение, не влияет
                # на дедуп/категории/photo_registry. get-vh и
                # get-maps_stories сознательно НЕ фильтруются и
                # продолжают идти в organization/reviews как раньше.
                # ==========================
                pool = self._get_pool(clean_url)
                self.pool_stats[pool] = self.pool_stats.get(pool, 0) + 1

                if pool == "get-vh":
                    self.video_previews.add(clean_url)
                elif pool == "get-maps_stories":
                    self.story_previews.add(clean_url)

                if self.current_photo_source == "organization":
                    self.organization_photos.add(clean_url)
                else:
                    self.review_photos.add(clean_url)

                # вся логика дедупликации/качества/категории — в одном месте
                self._register_photo(clean_url, self.current_photo_source)

                self._log(
                    f"PHOTO [{self.current_photo_source}]: {clean_url[:80]}"
                )

            except Exception as e:
                self._log(f"Ошибка обработки фото: {e}")

        try:
            with sync_playwright() as p:
                self._playwright = p

                self._log(f"FINAL HEADLESS BEFORE LAUNCH: {self.headless}")
                self._log(f"PLAYWRIGHT EXECUTABLE: {p.chromium.executable_path}")

                try:
                    self._browser = p.chromium.launch(
                        # ВРЕМЕННО: жёстко headless=False вместо self.headless,
                        # чтобы гарантированно увидеть окно, пока не разобрались,
                        # откуда бралось незаметное headless=True. Как только
                        # найдём и починим источник — вернуть headless=self.headless.
                        headless=False,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--start-maximized",
                        ]
                    )
                except Exception as e:
                    self._log(f"Chromium launch error: {e}")
                    raise
                self._page = self._browser.new_page()
                self._log("PAGE CREATED")
                self._page.on("response", handle_response)

                self._log(f"Открываем страницу: {url}")

                # открываем именно карточку организации
                base_url = url.split("/gallery/")[0].split("/reviews/")[0]

                self._page.goto(
                    base_url,
                    wait_until="domcontentloaded"
                )
                self._log("PAGE LOADED")
                self.current_photo_source = None
                self._page.wait_for_timeout(
                    3000 if ("/gallery/" in url or "photos[business]" in url) else 5000
                )

                # ИСПРАВЛЕНО: раньше паспорт собирался только если в исходном
                # URL уже была /gallery/ или photos[business]. Для обычной
                # ссылки на карточку организации (самый частый случай)
                # паспорт не собирался вообще, и все файлы получали имя
                # "organization_001.jpg" вместо реального названия.
                # Теперь паспорт собирается всегда, сразу после первой загрузки.
                self._collect_passport()
                self._log(
                    f"Собраны данные карточки: {self.passport.get('name', 'Неизвестно')}"
                )

                self._log("Начинаем сбор фотографий...")

                # ==========================
                # Фото организации
                # ==========================

                self.current_photo_source = "organization"

                # строим чистую ссылку галереи
                gallery_url = url.split("?")[0]

                gallery_url = (
                    gallery_url
                    .replace("/reviews/", "/")
                    .replace("/gallery/", "/")
                )

                gallery_url = gallery_url.rstrip("/") + "/gallery/"

                self._log(f"Открываем галерею организации: {gallery_url}")

                self._page.goto(
                    gallery_url,
                    wait_until="domcontentloaded"
                )

                # даём Яндексу только стартовый lazy-load
                self._page.wait_for_timeout(3000)

                # первый мягкий толчок, чтобы появились первые фото
                self._page.mouse.wheel(0, 500)

                self._page.wait_for_timeout(2000)

                self._scroll_and_collect(
                    counter=lambda: len(self.organization_photos),
                    label="ORG",
                    done_message="Галерея организации полностью загружена."
                )

                # ==========================
                # Фото отзывов
                # ==========================

                self.current_photo_source = "reviews"

                reviews_url = gallery_url.replace("/gallery/", "/reviews/")

                self._log(f"Открываем отзывы: {reviews_url}")

                self._page.goto(
                    reviews_url,
                    wait_until="domcontentloaded"
                )

                self._page.wait_for_timeout(3000)

                self._scroll_and_collect(
                    counter=lambda: len(self.review_photos),
                    label="REV",
                    done_message="Отзывы полностью загружены."
                )

                # ==========================
                # Итог
                # ==========================
                # ИСПРАВЛЕНО: раньше здесь был отдельный блок, который
                # заново сопоставлял review-фото с organization-фото по
                # _photo_key, чтобы подменить URL на более качественный.
                # Это дублировало работу, которую уже делает
                # _register_photo() в реальном времени (лучшее качество
                # и приоритет категории "reviews" сохраняются в
                # self.photo_registry / self.photo_categories по мере
                # поступления фото). Блок был не просто лишним, а ещё и
                # бесполезным: он менял self.review_photos, которое
                # больше нигде не участвует в формировании результата.

                dupes = self._raw_registered_count - len(self.photo_registry)

                self._log(
                    f"Организация: {len(self.organization_photos)}, "
                    f"Отзывы: {len(self.review_photos)}, "
                    f"Дубли: {dupes}, "
                    f"Игнорировано: {len(self.ignored_photos)}"
                )
                self._log(f"Итого уникальных фото: {len(self.photo_registry)}")

                if self.DEBUG:
                    self._log(f"Video previews: {len(self.video_previews)}")
                    self._log(f"Stories: {len(self.story_previews)}")

                    self._log("===== POOL STATS =====")
                    for pool, count in sorted(
                        self.pool_stats.items(), key=lambda item: -item[1]
                    ):
                        dots = "." * max(1, 22 - len(pool))
                        self._log(f"{pool} {dots} {count}")
                    self._log("=======================")

                # === СОХРАНЯЕМ ПАСПОРТ ===
                if self.passport and self.passport.get('name'):
                    safe_name = self.passport['name'].replace(' ', '_').replace('/', '_')
                    passport_path = Path(f"passports/{safe_name}_passport.json")
                    passport_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(passport_path, 'w', encoding='utf-8') as f:
                        json.dump(self.passport, f, ensure_ascii=False, indent=4)
                    self._log(f"✅ Паспорт сохранён: {passport_path}")

        except Exception as e:
            if self._is_cancelled:
                raise CancelledError("Парсинг отменён пользователем")
            raise ParserError(f"Ошибка парсинга: {e}")
        finally:
            self._close_browser()

        # ИСПРАВЛЕНО: раньше здесь бралась self.photo_categories.get(photo_url, "")
        # где photo_url — это уже полный URL лучшего качества, а
        # photo_categories ключуется нормализованным _photo_key(url).
        # Полный URL и его ключ — разные строки, поэтому категория
        # почти всегда возвращалась пустой, и is_review вычислялся
        # отдельно (и тоже некорректно) через self.review_photos,
        # который вообще никогда не заполнялся. Теперь категория и URL
        # берутся по одному и тому же ключу _photo_order, а is_review
        # выводится прямо из итоговой категории.
        photos = []

        for i, key in enumerate(
            (k for k in self._photo_order if k in self.photo_registry),
            start=1
        ):
            photo_url = self.photo_registry[key]
            category = self.photo_categories.get(key, "")

            photos.append(
                PhotoInfo(
                    url=photo_url,
                    filename=self._make_filename(i, category),
                    source=self._source_type,
                    status=ImportStatus.PENDING,
                    category=category,
                    is_review=(category == "reviews"),
                )
            )

        return photos

    def _photo_key(self, url: str) -> str:
        """
        Одинаковый идентификатор фото Яндекса.
        Разные размеры (S / M / L / XL / XXL / XXXL) считаем одним фото.
        """

        if not url:
            return ""

        parts = url.split("/")

        if parts and parts[-1] in self.QUALITY_RANK:
            parts = parts[:-1]

        return "/".join(parts)

    def _get_pool(self, url: str) -> str:
        """
        Достаёт "пул" — сегмент пути сразу после домена
        (get-altay, get-vh, get-maps_stories, ...). Используется
        только для статистики pool_stats, не влияет на дедуп.
        """
        try:
            return url.split("avatars.mds.yandex.net/")[1].split("/")[0]
        except Exception:
            return "?"

    def _register_photo(self, url: str, source: Optional[str]):
        """
        Единая точка регистрации фото — используется и из handle_response,
        и (при необходимости) из любого другого места сбора.

        Логика:
        - одно и то же фото Яндекс может отдавать в S/M/.../XXXL —
          сохраняем ссылку самого высокого качества;
        - если фото встретилось и в организации, и в отзывах —
          категория всегда становится "reviews";
        - source=None означает "фото до входа в галерею/отзывы"
          (например, первая загрузка карточки) — фото регистрируется
          в реестре, но без категории, как и раньше.
        """

        key = self._photo_key(url)

        if not key:
            return

        self._raw_registered_count += 1

        # ==========================
        # Лучшее качество
        # ==========================

        def quality(photo_url: str) -> int:
            return self.QUALITY_RANK.get(photo_url.split("/")[-1], 0)

        old_url = self.photo_registry.get(key)

        if old_url:
            if quality(url) > quality(old_url):
                self.photo_registry[key] = url
        else:
            self.photo_registry[key] = url

        # ==========================
        # Категория
        # ==========================

        if source:
            old_category = self.photo_categories.get(key)

            # если уже отзывное — ничего не меняем, reviews всегда сильнее
            if old_category == "reviews":
                pass
            elif source == "reviews":
                self.photo_categories[key] = "reviews"
            elif source == "organization":
                if not old_category:
                    self.photo_categories[key] = "organization"

        # ==========================
        # Порядок обнаружения (для стабильной нумерации файлов)
        # ==========================

        if key not in self._photo_order_set:
            self._photo_order_set.add(key)
            self._photo_order.append(key)
        # ИСПРАВЛЕНО: временный self._log("DEBUG POOL ...") отсюда убран —
        # он свою задачу выполнил (нашли get-vh/get-maps_stories), и теперь
        # эта же информация собирается постоянно через self.pool_stats
        # в handle_response, без изменения логики самой регистрации фото.

    def _get_scroll_height(self) -> Optional[int]:
        """
        Высота документа — дополнительный (необязательный) сигнал того,
        что подгрузка реально закончилась, а не просто "фото пока не
        пришли". Если сайт скроллит не document, а внутренний div,
        это просто вернёт None/не изменится, и скролл упадёт обратно
        на обычный stable_threshold по количеству фото — без регрессии.
        """
        try:
            return self._page.evaluate("document.documentElement.scrollHeight")
        except Exception:
            return None

    def _try_click_more_button(self) -> None:
        """
        Некоторые карточки вместо бесконечного скролла в какой-то момент
        показывают кнопку «Показать ещё» — обычный wheel-скролл её не
        триггерит, и подгрузка молча останавливается. Пробуем найти и
        нажать; если кнопки нет — тихо выходим, это нормальная ситуация.
        """

        try:
            button = self._page.get_by_text("Показать ещё", exact=False).first
            if button.count() and button.is_visible():
                button.click(timeout=1000)
                self._page.wait_for_timeout(500)
        except Exception:
            pass

    def _scroll_and_collect(
        self,
        counter,
        label: str,
        done_message: str,
        wheel_delta: int = 250,
        wait_ms: int = 700,
        max_iterations: int = 600,
        stable_threshold: int = 25,
        height_stable_threshold: int = 20,
        heartbeat_every: int = 8,
        phase_timeout_sec: float = 120.0,
        min_iterations_before_quick_exit: int = 15,
    ) -> None:
        """
        Скролл маленькими частыми шагами (имитация обычного пользователя,
        который листает потихоньку) — вместо редких больших прыжков.

        ИСПРАВЛЕНО: раньше wheel_delta=900 мог "перепрыгивать" через
        элементы виртуализированной галереи так быстро, что часть из
        них вообще не успевала запросить картинку и терялась навсегда
        (галерея заканчивалась на 61 вместо ~150+ реальных фото). Плюс
        предыдущий "быстрый выход" по высоте страницы мог сработать
        прямо во время паузы Яндекса между пачками lazy-load, а не
        когда фото реально закончились — добавил
        `min_iterations_before_quick_exit`, чтобы он не срабатывал
        подозрительно рано.

        Останавливается по первому из:
        - количество фото не растёт `stable_threshold` итераций подряд;
        - ИЛИ (после `min_iterations_before_quick_exit` итераций)
          количество фото и высота страницы одновременно не растут
          `height_stable_threshold` итераций — более быстрый выход,
          но уже не такой нервный, как раньше;
        - `phase_timeout_sec` — предохранитель по времени;
        - `max_iterations` попыток скролла.
        """

        phase_started = time.time()

        previous_count = 0
        stable_count = 0
        seen_any = False
        last_log_count = 0

        previous_height = self._get_scroll_height()
        height_stable_count = 0

        for i in range(max_iterations):

            if self._is_cancelled:
                break

            if time.time() - phase_started > phase_timeout_sec:
                self._log(
                    f"[{label}] Таймаут фазы ({phase_timeout_sec:.0f}с), "
                    f"останавливаемся принудительно. Фото: {counter()}"
                )
                return

            # маленький шаг вниз — как обычная прокрутка колесом мыши
            self._page.mouse.wheel(0, wheel_delta)

            # ждём подгрузку новых фото
            self._page.wait_for_timeout(wait_ms)

            # на некоторых карточках подгрузку нужно триггерить кнопкой,
            # а не только скроллом
            self._try_click_more_button()

            current_count = counter()
            current_height = self._get_scroll_height()

            if current_count != last_log_count:
                self._log(
                    f"[{label} {i+1}/{max_iterations}] Фото: {current_count}"
                )
                last_log_count = current_count
            elif seen_any and stable_count > 0 and stable_count % heartbeat_every == 0:
                self._log(
                    f"[{label}] Новых фото нет, ждём стабилизации "
                    f"({stable_count}/{stable_threshold})..."
                )

            if current_count > 0:
                seen_any = True

            if current_count > previous_count:
                stable_count = 0
            elif seen_any:
                stable_count += 1
            previous_count = current_count

            if current_height is not None and previous_height is not None \
                    and current_height > previous_height:
                height_stable_count = 0
            elif seen_any:
                height_stable_count += 1
            previous_height = current_height

            height_confirms_done = (
                current_height is not None
                and height_stable_count >= height_stable_threshold
            )

            quick_exit_allowed = i >= min_iterations_before_quick_exit

            ready_to_finish = seen_any and (
                stable_count >= stable_threshold
                or (quick_exit_allowed and height_confirms_done)
            )

            if ready_to_finish:

                self._log(f"[{label}] Последняя проверка загрузки...")

                before = counter()

                self._try_click_more_button()

                # маленький дополнительный толчок
                self._page.mouse.wheel(0, wheel_delta)

                # ждём lazy-load
                self._page.wait_for_timeout(3000)

                after = counter()

                self._log(f"[{label}] Финальная проверка: {before}->{after}")

                # пришли новые фото — продолжаем
                if after > before:
                    stable_count = 0
                    height_stable_count = 0
                    previous_count = after
                    continue

                self._log(f"{done_message} Фото: {after}")
                return

        self._log(
            f"[{label}] Достигнут лимит итераций ({max_iterations}), "
            f"останавливаемся принудительно."
        )

    def _log(self, message: str) -> None:
        print(f"[YandexParser] {message}")

    def _close_browser(self) -> None:

        if self._page:
            try:
                self._page.close(run_before_unload=False)
            except Exception:
                pass
            finally:
                self._page = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            finally:
                self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            finally:
                self._playwright = None

    def cancel(self) -> None:
        self._is_cancelled = True

    def close(self) -> None:
        self._close_browser()

    def _make_filename(self, index, category=None):
        name = self.passport.get("name") or "organization"
        name = name.replace(" ", "_").replace("/", "_")

        if category:
            return f"{name}_{category}_{index:03}.jpg"

        return f"{name}_{index:03}.jpg"

    def _collect_passport(self):
        """Сбор паспорта организации без мусора Яндекс интерфейса."""

        try:
            self.passport = {
                "name": "",
                "address": "",
                "phone": "",
                "website": "",
                "worktime": "",
                "rubrics": [],
                "metro": "",
                "yandex_url": self._page.url if self._page else ""
            }

            # ==========================
            # Название
            # ==========================

            # ИСПРАВЛЕНО: карточка иногда ещё не успевает отрисовать h1
            # к моменту сбора паспорта. Вместо wait_for_load_state
            # ("networkidle") — рискованно на SPA с поллингом/вебсокетами,
            # где сеть может никогда не "затихнуть", и это способно
            # вызвать зависание того же рода, что мы чинили выше —
            # делаем несколько коротких попыток с паузой.
            name = ""
            for attempt in range(3):
                try:
                    name = (
                        self._page.locator('h1.business-title-view__name')
                        .first
                        .inner_text(timeout=2000)
                        .strip()
                    )
                except Exception:
                    try:
                        name = (
                            self._page.locator("h1")
                            .first
                            .inner_text(timeout=1000)
                            .strip()
                        )
                    except Exception:
                        name = ""

                if name:
                    break

                self._page.wait_for_timeout(1000)

            self.passport["name"] = name

            # ==========================
            # Адрес
            # ==========================

            try:
                # NB: селектор не проверен на живой странице — если
                # вёрстка Яндекса отличается, здесь может понадобиться
                # правка под конкретный класс блока с адресом.
                addr_bad_words = ["маршрут", "route", "показать на карте"]

                candidates = self._page.locator(
                    '[class*="business-contacts-view"] a'
                ).all()

                for addr in candidates:
                    text = addr.inner_text(timeout=1000).strip()

                    if not text:
                        continue

                    if any(bad in text.lower() for bad in addr_bad_words):
                        continue

                    self.passport["address"] = text
                    break

            except Exception:
                pass

            # ==========================
            # Телефон
            # ==========================

            try:
                phone = self._page.locator('a[href^="tel:"]').first

                if phone.count():
                    self.passport["phone"] = phone.inner_text().strip()

            except Exception:
                pass

            # ==========================
            # Сайт
            # ==========================

            try:
                links = self._page.locator('a[href^="http"]').all()

                for link in links:

                    href = link.get_attribute("href")

                    if not href:
                        continue

                    bad = ["yandex.ru", "legal", "maps", "yastatic"]

                    if any(x in href for x in bad):
                        continue

                    self.passport["website"] = href
                    break

            except Exception:
                pass

            # ==========================
            # Рубрики
            # ==========================

            try:
                items = self._page.locator(
                    '[class*="business-card-title-view"]'
                ).all()

                result = []

                for item in items:
                    text = item.inner_text().strip()

                    if text and len(text) < 100:
                        result.append(text)

                self.passport["rubrics"] = result[:5]

            except Exception:
                pass

            # ==========================
            # Время работы
            # ==========================

            try:
                work = self._page.locator('[class*="work-hours"]').first

                if work.count():
                    self.passport["worktime"] = work.inner_text().strip()

            except Exception:
                pass

            self._log(f"Паспорт собран: {self.passport.get('name')}")

        except Exception as e:
            self._log(f"Паспорт не удалось собрать: {e}")

    def supports_url(self, url: str) -> bool:
        return "yandex.ru/maps" in url or "yandex.by/maps" in url

    # TODO: видео — после того как фото будут собираться идеально на
    # любой карточке. План: не через response.text(), а через JS/
    # Performance API из состояния плеера — искать manifest.mpd или
    # master.m3u8.
    #
    # TODO: сторис — отложено до доступа владельца в Яндекс Бизнесе
    # (или до доказательства, что они видны и без него). То, что мы
    # нашли в панели Яндекс Бизнеса — это форма ЗАГРУЗКИ сторис
    # (get-maps_stories, суффикс качества в пикселях WxH), а не то,
    # как они отображаются на публичной карточке yandex.ru/maps —
    # писать код сбора вслепую сейчас смысла нет.


class GoogleParser(BaseParser):
    """Парсер Google Maps (заглушка)."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        super().__init__(headless=headless, timeout=timeout)
        self._source_type = SourceType.GOOGLE

    def parse(self, url: str) -> List[PhotoInfo]:
        # TODO: Реализовать парсинг Google Maps
        return []

    def supports_url(self, url: str) -> bool:
        return "google.com/maps" in url


class TwoGISParser(BaseParser):
    """Парсер 2GIS (заглушка)."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        super().__init__(headless=headless, timeout=timeout)
        self._source_type = SourceType.TWOGIS

    def parse(self, url: str) -> List[PhotoInfo]:
        # TODO: Реализовать парсинг 2GIS
        return []

    def supports_url(self, url: str) -> bool:
        return "2gis.ru" in url
