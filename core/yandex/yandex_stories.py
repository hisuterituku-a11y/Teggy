"""
Изменения относительно прошлой версии:

1. УБРАНО: cards.count() как источник истины / стоп-условие. Живой тест
   показал, что счётчик вообще не двигался при прокрутке (лента обложек
   виртуализирована через CSS transform, а не native scroll — обычный
   page.mouse.wheel() по ней не сработал, курсор не наведён на элемент),
   плюс, похоже, это счётчик ГРУПП историй, а не отдельных слайдов.
   Из-за этого сбор останавливался почти сразу на 10-15 вместо ожидаемых
   80-100. cards.count() оставлен только как диагностическая подсказка
   в логе, никогда не используется для решения "хватит/не хватит".

2. ДОБАВЛЕНО: дедупликация по хешу фото, а не по полному URL. Яндекс
   отдаёт один и тот же слайд в двух вариантах (/orig и /1080x1920) —
   раньше оба считались как 2 разных найденных фото. Теперь ключом
   является часть URL до суффикса размера, а из двух вариантов
   сохраняется /orig (оригинальное качество).

3. Тайм-аут и порог тишины больше НЕ завязаны на предполагаемое целевое
   число (оно теперь не используется вообще) — единый щедрый лимит по
   времени + патиентное молчание с несколькими попытками nudge, без
   привязки к ненадёжному счётчику.
"""

from pathlib import Path
from typing import List, Callable
import time
import requests

from playwright.sync_api import sync_playwright


class YandexStoriesDownloader:

    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self._cancelled = False

    def _log(self, text, callback=None):
        print("[Stories]", text)
        if callback:
            callback(text)

    # ==================================================
    # Ключ дедупликации: URL без суффикса размера (/orig, /1080x1920, ...)
    # ==================================================

    @staticmethod
    def _story_key(url: str) -> str:
        if url.endswith("/orig"):
            return url[: -len("/orig")]
        # /1080x1920, /720x1280 и т.п. — обрезаем последний сегмент пути
        parts = url.rsplit("/", 1)
        if len(parts) == 2 and "x" in parts[1] and parts[1][0].isdigit():
            return parts[0]
        return url

    # ==================================================
    # Попытка "подтолкнуть" воспроизведение при застревании
    # ==================================================

    def _nudge(self, page, on_log=None) -> None:
        try:
            page.keyboard.press("ArrowRight")
            self._log("Nudge: ArrowRight", on_log)
            return
        except Exception:
            pass

        try:
            next_btn = page.locator(".story-screen-view__next").first
            if next_btn.count():
                next_btn.click(force=True, timeout=1000)
                self._log("Nudge: click(force=True) по next", on_log)
        except Exception as e:
            self._log(f"Nudge не удался: {e}", on_log)

    # ==================================================
    # COLLECT
    # ==================================================

    def collect(
        self,
        url: str,
        on_log: Callable = None,
        max_wait_seconds: float = 480.0,   # 8 минут — щедрый предохранитель
        stall_threshold: int = 10,         # секунд тишины до nudge
        max_nudges: int = 12,
        # секунд тишины ПОСЛЕ последнего nudge без роста — считаем концом
        final_stall_after_nudge: int = 15,
    ) -> List[str]:

        # ключ (без суффикса размера) -> лучший найденный URL для него
        story_registry: dict = {}
        # сохраняем порядок первого обнаружения — для стабильной нумерации
        story_order: List[str] = []

        def add_url(img_url: str) -> None:
            key = self._story_key(img_url)

            is_new_key = key not in story_registry

            # /orig всегда предпочтительнее /1080x1920 и т.п.
            current = story_registry.get(key)
            if current is None or (img_url.endswith("/orig") and not current.endswith("/orig")):
                story_registry[key] = img_url

            if is_new_key:
                story_order.append(key)
                self._log(f"Найдена оригинальная story: {len(story_registry)}", on_log)

        with sync_playwright() as p:

            self._log("Открываем Яндекс Карты", on_log)

            browser = p.chromium.launch(headless=self.headless)

            context = browser.new_context(
                viewport={"width": 1400, "height": 900},
                user_agent="Mozilla/5.0 Windows NT 10.0 Chrome/120",
            )

            page = context.new_page()

            def response_handler(response):
                if self._cancelled:
                    return
                try:
                    response_url = response.url
                    if "get-maps_stories" not in response_url:
                        return
                    if not ("/orig" in response_url or "1080x" in response_url):
                        return
                    add_url(response_url)
                except Exception:
                    pass

            page.on("response", response_handler)

            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
            page.wait_for_timeout(5000)
            self._log("Страница открыта", on_log)

            cards = page.locator(".story-cover-preview")
            cards_count = cards.count()
            # ИЗМЕНЕНО: это ТОЛЬКО диагностика, больше нигде не используется
            self._log(
                f"Карточек Stories в DOM (справочно, НЕ используется "
                f"как цель — этот счётчик оказался ненадёжным): {cards_count}",
                on_log,
            )

            if cards_count == 0:
                browser.close()
                return []

            try:
                cards.first.click(force=True)
                self._log("Stories viewer открыт", on_log)
            except Exception as e:
                self._log(f"Ошибка открытия viewer: {e}", on_log)
                browser.close()
                return []

            self._log("Ждём загрузку оригиналов...", on_log)

            phase_started = time.time()
            last_count = -1
            stable_seconds = 0
            nudges_done = 0
            seconds_since_last_nudge = 0
            nudge_active = False

            while True:
                if self._cancelled:
                    break

                elapsed = time.time() - phase_started
                if elapsed > max_wait_seconds:
                    self._log(
                        f"Достигнут общий тайм-аут ({max_wait_seconds:.0f}с), "
                        f"собрано {len(story_registry)}",
                        on_log,
                    )
                    break

                page.wait_for_timeout(1000)
                current = len(story_registry)

                if current == last_count:
                    stable_seconds += 1
                    if nudge_active:
                        seconds_since_last_nudge += 1
                else:
                    stable_seconds = 0
                    seconds_since_last_nudge = 0
                    nudge_active = False
                last_count = current

                self._log(f"Получено оригиналов: {current}", on_log)

                # реальный конец: тишина уже ПОСЛЕ nudge-попытки, и
                # достаточно долго после неё
                if nudge_active and seconds_since_last_nudge >= final_stall_after_nudge:
                    self._log(
                        f"Тишина {final_stall_after_nudge}с после последнего nudge — "
                        f"считаем, что Stories закончились ({current})",
                        on_log,
                    )
                    break

                # застряли, ещё не пробовали толкнуть — пробуем
                if stable_seconds >= stall_threshold and not nudge_active:
                    if nudges_done < max_nudges:
                        self._nudge(page, on_log)
                        nudges_done += 1
                        nudge_active = True
                        seconds_since_last_nudge = 0
                    else:
                        self._log(
                            f"Исчерпан лимит nudge ({max_nudges}), "
                            f"собрано {current}",
                            on_log,
                        )
                        break

            self._log("Загрузка Stories завершена", on_log)

            try:
                page.keyboard.press("Escape")
            except Exception:
                pass

            browser.close()

        result = [story_registry[key] for key in story_order]

        self._log(f"Stories найдено (уникальных): {len(result)}", on_log)
        return result

    # ==================================================
    # DOWNLOAD — без изменений
    # ==================================================

    def download(self, urls: List[str], folder: Path):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        saved = 0

        for index, url in enumerate(urls, start=1):
            if self._cancelled:
                break
            try:
                response = requests.get(
                    url, timeout=30, headers={"User-Agent": "Mozilla/5.0"}
                )
                response.raise_for_status()
                path = folder / f"story_{index:03}.jpg"
                with open(path, "wb") as f:
                    f.write(response.content)
                saved += 1
                print("[Stories] saved", path.name)
            except Exception as e:
                print("[Stories] ошибка:", e)

        return saved

    def cancel(self):
        self._cancelled = True