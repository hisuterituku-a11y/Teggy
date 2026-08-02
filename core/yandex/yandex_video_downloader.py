from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urlsplit, urlunsplit

from playwright.sync_api import Browser, Page, sync_playwright

from core.yandex.dash_downloader import DashDownloader


LogCallback = Callable[[str], None]


class YandexVideoDownloader:
    """Собирает DASH-манифесты и сохраняет видео из Яндекс Карт."""

    def __init__(self, headless: bool = True, timeout: int = 60) -> None:
        self.headless = headless
        self.timeout = timeout
        self._cancelled = False
        self._browser: Browser | None = None

    def _log(self, text: str, on_log: LogCallback | None = None) -> None:
        if on_log:
            on_log(text)
        else:
            print(f"[YandexVideoDownloader] {text}")

    @staticmethod
    def _extract_video_id(url: str) -> str | None:
        match = re.search(r"\b(vpl[a-zA-Z0-9_-]+)\b", unquote(url))
        return match.group(1) if match else None

    @classmethod
    def _manifest_key(cls, url: str) -> str:
        return cls._extract_video_id(url) or url.split("?", 1)[0]

    @staticmethod
    def _is_manifest_response(url: str, content_type: str) -> bool:
        lower_url = url.lower()
        lower_type = content_type.lower()
        return (
            "manifest.mpd" in lower_url
            or lower_url.endswith(".mpd")
            or ".mpd?" in lower_url
            or "application/dash+xml" in lower_type
        )

    @staticmethod
    def _make_gallery_url(url: str) -> str:
        parts = urlsplit(url)
        path = parts.path.rstrip("/")
        if "/gallery" in path:
            path = path.split("/gallery", 1)[0]
        return urlunsplit(
            (
                parts.scheme or "https",
                parts.netloc or "yandex.ru",
                path + "/gallery/",
                parts.query,
                "",
            )
        )

    @staticmethod
    def _find_bundled_chromium() -> str | None:
        roots: list[Path] = []
        if getattr(sys, "frozen", False):
            roots.extend(
                [
                    Path(sys.executable).resolve().parent,
                    Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)),
                ]
            )
        roots.append(Path(__file__).resolve().parents[2])

        relative = Path("playwright") / "driver" / "package" / ".local-browsers"
        candidates: list[Path] = []
        for root in roots:
            candidates.extend(
                [
                    root / "_internal" / relative,
                    root / relative,
                ]
            )

        for browser_dir in candidates:
            if not browser_dir.is_dir():
                continue
            matches = sorted(browser_dir.glob("chromium-*/chrome-win*/chrome.exe"))
            if matches:
                return str(matches[-1].resolve())
        return None

    def _open_gallery(
        self,
        page: Page,
        organization_url: str,
        on_log: LogCallback | None,
    ) -> None:
        gallery_url = self._make_gallery_url(organization_url)
        self._log(f"Открываем галерею: {gallery_url}", on_log)
        page.goto(
            gallery_url,
            wait_until="domcontentloaded",
            timeout=self.timeout * 1000,
        )
        page.wait_for_timeout(5000)
        self._log(f"Текущая страница: {page.url}", on_log)

    def _open_first_gallery_item(
        self,
        page: Page,
        on_log: LogCallback | None,
    ) -> None:
        selectors = (
            "a[href*='photos%5Bid%5D']",
            "a[href*='photos[id]']",
            "a[href*='photos']",
            "[class*='gallery'] [role='button']",
            "[class*='gallery'] img",
            "[class*='photo'] img",
        )
        for selector in selectors:
            try:
                locator = page.locator(selector)
                for index in range(min(locator.count(), 40)):
                    try:
                        item = locator.nth(index)
                        if not item.is_visible():
                            continue
                        box = item.bounding_box()
                        if not box or box["width"] < 80 or box["height"] < 80:
                            continue
                        item.scroll_into_view_if_needed(timeout=3000)
                        item.click(force=True, timeout=3000)
                        page.wait_for_timeout(1200)
                        self._log(
                            f"Первый материал открыт через: {selector}", on_log
                        )
                        return
                    except Exception:
                        continue
            except Exception:
                continue
        raise RuntimeError("Не удалось открыть первый материал галереи")

    @staticmethod
    def _play_current_video(page: Page) -> None:
        try:
            videos = page.locator("video")
            if videos.count() == 0:
                return
            videos.last.evaluate(
                """
                video => {
                    video.muted = true;
                    video.autoplay = true;
                    const result = video.play();
                    if (result && result.catch) result.catch(() => {});
                }
                """
            )
        except Exception:
            pass

    @staticmethod
    def _current_signature(page: Page) -> str:
        try:
            return str(
                page.evaluate(
                    """
                    () => {
                        const media = [...document.querySelectorAll('video, img')]
                            .filter((element) => {
                                const rect = element.getBoundingClientRect();
                                const style = getComputedStyle(element);
                                return rect.width > 250 && rect.height > 250 &&
                                    style.display !== 'none' &&
                                    style.visibility !== 'hidden';
                            })
                            .sort((left, right) => {
                                const a = left.getBoundingClientRect();
                                const b = right.getBoundingClientRect();
                                return b.width * b.height - a.width * a.height;
                            });
                        const element = media[0];
                        if (!element) return location.href;
                        return [
                            location.href,
                            element.currentSrc || '',
                            element.src || '',
                            element.poster || '',
                            element.getAttribute('data-id') || '',
                            element.getAttribute('data-photo-id') || ''
                        ].join('|');
                    }
                    """
                )
            )
        except Exception:
            return page.url

    def _walk_gallery(
        self,
        page: Page,
        manifests: list[str],
        on_log: LogCallback | None,
        max_items: int = 150,
    ) -> None:
        self._log("Открываем просмотрщик и обходим материалы галереи", on_log)
        self._open_first_gallery_item(page, on_log)
        seen_signatures: set[str] = set()
        repeated = 0
        no_new_video = 0

        for index in range(max_items):
            if self._cancelled:
                return
            before = len(manifests)
            self._play_current_video(page)
            page.wait_for_timeout(1400)
            signature = self._current_signature(page)
            if signature in seen_signatures:
                repeated += 1
            else:
                seen_signatures.add(signature)
                repeated = 0

            if len(manifests) > before:
                no_new_video = 0
                self._log(
                    f"Новый manifest перехвачен; всего: {len(manifests)}", on_log
                )
            else:
                no_new_video += 1

            if index % 10 == 0:
                self._log(
                    f"Галерея: материал {index + 1}/{max_items}; "
                    f"видео найдено: {len(manifests)}",
                    on_log,
                )
            if repeated >= 3:
                self._log("Материалы начали повторяться, обход завершён", on_log)
                break
            if manifests and no_new_video >= 30:
                self._log(
                    "Новых видео нет 30 материалов подряд, обход завершён", on_log
                )
                break
            try:
                page.keyboard.press("ArrowRight")
                page.wait_for_timeout(350)
            except Exception as error:
                self._log(
                    f"Не удалось перейти к следующему материалу: {error}", on_log
                )
                break

    def collect(
        self,
        url: str,
        on_log: LogCallback | None = None,
    ) -> list[str]:
        self._cancelled = False
        manifests: list[str] = []
        keys: set[str] = set()
        browser: Browser | None = None

        try:
            with sync_playwright() as playwright:
                self._log("Запуск браузера для поиска видео", on_log)
                launch_kwargs: dict[str, object] = {
                    "headless": self.headless,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--autoplay-policy=no-user-gesture-required",
                        "--mute-audio",
                    ],
                }
                bundled_chromium = self._find_bundled_chromium()
                if bundled_chromium:
                    launch_kwargs["executable_path"] = bundled_chromium
                    self._log(
                        f"Используется встроенный Chromium: {bundled_chromium}",
                        on_log,
                    )
                browser = playwright.chromium.launch(**launch_kwargs)
                self._browser = browser
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    locale="ru-RU",
                )
                page = context.new_page()

                def handle_response(response) -> None:
                    if self._cancelled:
                        return
                    try:
                        content_type = response.headers.get("content-type", "")
                        manifest_url = response.url
                        if not self._is_manifest_response(manifest_url, content_type):
                            return
                        key = self._manifest_key(manifest_url)
                        if key in keys:
                            return
                        keys.add(key)
                        manifests.append(manifest_url)
                        video_id = self._extract_video_id(manifest_url)
                        suffix = f" ({video_id})" if video_id else ""
                        self._log(
                            f"Видео найдено: {len(manifests)}{suffix}", on_log
                        )
                    except Exception:
                        pass

                page.on("response", handle_response)
                self._open_gallery(page, url, on_log)
                if not self._cancelled:
                    self._walk_gallery(page, manifests, on_log)
                page.wait_for_timeout(1500)
        except Exception as error:
            self._log(f"Ошибка при сборе видео: {error}", on_log)
            raise RuntimeError(f"Не удалось собрать видео: {error}") from error
        finally:
            self._browser = None
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass

        self._log(f"Сбор видео завершён: {len(manifests)}", on_log)
        return manifests

    @staticmethod
    def _find_ffmpeg() -> str | None:
        roots: list[Path] = []
        if getattr(sys, "frozen", False):
            roots.append(Path(sys.executable).resolve().parent)
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                roots.append(Path(meipass))
        roots.extend([Path.cwd(), Path(__file__).resolve().parents[2]])
        relatives = (
            Path("ffmpeg.exe"),
            Path("_internal") / "ffmpeg.exe",
            Path("bin") / "ffmpeg.exe",
            Path("tools") / "ffmpeg.exe",
            Path("ffmpeg") / "bin" / "ffmpeg.exe",
        )
        for root in roots:
            for relative in relatives:
                candidate = root / relative
                if candidate.is_file():
                    return str(candidate.resolve())
        system_ffmpeg = shutil.which("ffmpeg")
        return system_ffmpeg or None

    def download(
        self,
        urls: list[str],
        folder: Path | str,
        on_log: LogCallback | None = None,
        skip_existing: bool = True,
    ) -> int:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        if not urls:
            self._log("Видео для скачивания не найдено", on_log)
            return 0

        ffmpeg_path = self._find_ffmpeg()
        if not ffmpeg_path:
            message = (
                "Не найден ffmpeg. Установи ffmpeg или положи ffmpeg.exe "
                "рядом с программой."
            )
            self._log(message, on_log)
            raise RuntimeError(message)

        self._log(f"Используется ffmpeg: {ffmpeg_path}", on_log)
        dash = DashDownloader(ffmpeg_path=ffmpeg_path, timeout=self.timeout)
        saved = skipped = failed = 0
        total = len(urls)

        for index, manifest_url in enumerate(reversed(urls), start=1):
            if self._cancelled:
                self._log("Скачивание видео отменено", on_log)
                break
            video_id = self._extract_video_id(manifest_url)
            filename = folder / (
                f"{video_id}.mp4" if video_id else f"video_{index:03}.mp4"
            )
            if skip_existing and filename.exists() and filename.stat().st_size > 1024:
                skipped += 1
                self._log(f"Видео {index}/{total}: уже существует", on_log)
                continue

            self._log(
                f"Скачивание видео {index}/{total} через локальные DASH-сегменты",
                on_log,
            )
            try:
                dash.download(
                    manifest_url,
                    filename,
                    on_log=on_log,
                    cancel=lambda: self._cancelled,
                )
            except Exception as error:
                failed += 1
                filename.unlink(missing_ok=True)
                self._log(
                    f"Видео {index}/{total}: не удалось скачать: {error}", on_log
                )
                continue
            saved += 1
            self._log(
                f"Видео скачано: {index}/{total}; "
                f"размер: {filename.stat().st_size / 1024 / 1024:.2f} МБ",
                on_log,
            )

        self._log(
            f"Видео сохранено: {saved}; пропущено: {skipped}; ошибок: {failed}",
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
