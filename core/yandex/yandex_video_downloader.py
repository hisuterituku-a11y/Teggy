from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urlsplit, urlunsplit

from playwright.sync_api import Browser, Page, sync_playwright


LogCallback = Callable[[str], None]


class YandexVideoDownloader:
    """Сбор и немедленное скачивание видео из галереи Яндекс Карт."""

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 60,
    ) -> None:
        self.headless = headless
        self.timeout = timeout
        self._cancelled = False
        self._browser: Browser | None = None
        self._manifest_headers: dict[str, dict[str, str]] = {}

    def _log(
        self,
        text: str,
        on_log: LogCallback | None = None,
    ) -> None:
        if on_log:
            on_log(text)
        else:
            print(f"[YandexVideoDownloader] {text}")

    @staticmethod
    def _extract_video_id(url: str) -> str | None:
        match = re.search(
            r"\b(vpl[a-zA-Z0-9_-]+)\b",
            unquote(url),
        )
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
            or ".m3u8" in lower_url
            or "mpegurl" in lower_type
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

    def _capture_manifest(
        self,
        response,
        context,
        pending: list[str],
        keys: set[str],
        on_log: LogCallback | None,
    ) -> None:
        try:
            url = response.url
            content_type = response.headers.get("content-type", "")
            if not self._is_manifest_response(url, content_type):
                return

            key = self._manifest_key(url)
            if key in keys:
                return

            request_headers = response.request.all_headers()
            cookies = context.cookies(url)
            cookie_header = "; ".join(
                f"{item['name']}={item['value']}"
                for item in cookies
            )

            headers = {
                "User-Agent": request_headers.get("user-agent", self.USER_AGENT),
                "Referer": request_headers.get(
                    "referer",
                    "https://yandex.ru/maps/",
                ),
                "Origin": request_headers.get("origin", "https://yandex.ru"),
                "Accept": request_headers.get("accept", "*/*"),
                "Accept-Language": request_headers.get(
                    "accept-language",
                    "ru-RU,ru;q=0.9,en;q=0.8",
                ),
            }
            if cookie_header:
                headers["Cookie"] = cookie_header

            keys.add(key)
            pending.append(url)
            self._manifest_headers[key] = headers

            video_id = self._extract_video_id(url)
            suffix = f" ({video_id})" if video_id else ""
            self._log(f"Видео найдено: {len(keys)}{suffix}", on_log)
        except Exception as error:
            self._log(
                f"Не удалось сохранить параметры manifest: {error}",
                on_log,
            )

    def _open_gallery(
        self,
        page: Page,
        url: str,
        on_log: LogCallback | None,
    ) -> None:
        gallery_url = self._make_gallery_url(url)
        self._log(f"Открываем галерею: {gallery_url}", on_log)
        page.goto(
            gallery_url,
            wait_until="domcontentloaded",
            timeout=self.timeout * 1000,
        )
        page.wait_for_timeout(5000)
        self._log(f"Текущая страница: {page.url}", on_log)

    def _open_first_item(
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
                    page.wait_for_timeout(1000)
                    self._log(
                        f"Первый материал открыт через: {selector}",
                        on_log,
                    )
                    return
                except Exception:
                    continue
        raise RuntimeError("Не удалось открыть первый материал галереи")

    @staticmethod
    def _play_video(page: Page) -> None:
        try:
            videos = page.locator("video")
            if videos.count() == 0:
                return
            videos.last.evaluate(
                """
                video => {
                    video.muted = true;
                    video.autoplay = true;
                    const promise = video.play();
                    if (promise && promise.catch) promise.catch(() => {});
                }
                """
            )
        except Exception:
            pass

    @staticmethod
    def _find_ffmpeg() -> str | None:
        system = shutil.which("ffmpeg")
        if system:
            return system
        for candidate in (
            Path("ffmpeg.exe"),
            Path("bin") / "ffmpeg.exe",
            Path("tools") / "ffmpeg.exe",
            Path("ffmpeg") / "bin" / "ffmpeg.exe",
        ):
            if candidate.exists():
                return str(candidate.resolve())
        return None

    @staticmethod
    def _format_headers(headers: dict[str, str]) -> str:
        return "".join(
            f"{name}: {value}\r\n"
            for name, value in headers.items()
            if value
        )

    def _run_ffmpeg(
        self,
        ffmpeg_path: str,
        manifest_url: str,
        filename: Path,
        headers: dict[str, str],
        on_log: LogCallback | None,
    ) -> bool:
        temp_path = filename.with_name(
            f"{filename.stem}.part{filename.suffix}"
        )
        error_path = filename.with_suffix(".mp4.ffmpeg.log")
        temp_path.unlink(missing_ok=True)
        error_path.unlink(missing_ok=True)

        command = [
            ffmpeg_path,
            "-y",
            "-nostdin",
            "-loglevel",
            "error",
            "-rw_timeout",
            "20000000",
            "-reconnect",
            "1",
            "-reconnect_streamed",
            "1",
            "-reconnect_at_eof",
            "1",
            "-reconnect_delay_max",
            "3",
            "-http_persistent",
            "0",
            "-multiple_requests",
            "0",
            "-user_agent",
            headers.get("User-Agent", self.USER_AGENT),
            "-headers",
            self._format_headers(headers),
            "-i",
            manifest_url,
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(temp_path),
        ]

        flags = (
            subprocess.CREATE_NO_WINDOW
            if hasattr(subprocess, "CREATE_NO_WINDOW")
            else 0
        )
        process: subprocess.Popen | None = None
        started = time.monotonic()
        last_growth = started
        last_size = 0

        try:
            with error_path.open(
                "w",
                encoding="utf-8",
                errors="replace",
            ) as error_file:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=error_file,
                    creationflags=flags,
                )

                while process.poll() is None:
                    if self._cancelled:
                        break
                    now = time.monotonic()
                    size = temp_path.stat().st_size if temp_path.exists() else 0
                    if size > last_size:
                        last_size = size
                        last_growth = now
                    if size == 0 and now - started >= 20:
                        break
                    if size > 0 and now - last_growth >= 45:
                        break
                    if now - started >= 600:
                        break
                    time.sleep(0.2)

                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)

            if process.returncode != 0:
                error_text = error_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).strip()
                if error_text:
                    self._log(
                        f"Ошибка ffmpeg: {error_text[-1800:]}",
                        on_log,
                    )
                temp_path.unlink(missing_ok=True)
                return False

            if not temp_path.exists() or temp_path.stat().st_size < 1024:
                temp_path.unlink(missing_ok=True)
                return False

            temp_path.replace(filename)
            self._log(
                f"Видео сохранено: {filename.stat().st_size / 1024 / 1024:.2f} МБ",
                on_log,
            )
            return True
        except Exception as error:
            if process is not None and process.poll() is None:
                try:
                    process.kill()
                except Exception:
                    pass
            temp_path.unlink(missing_ok=True)
            self._log(f"Ошибка запуска ffmpeg: {error}", on_log)
            return False
        finally:
            error_path.unlink(missing_ok=True)

    def _download_fresh_manifest(
        self,
        ffmpeg_path: str,
        manifest_url: str,
        folder: Path,
        index: int,
        skip_existing: bool,
        on_log: LogCallback | None,
    ) -> tuple[bool, bool]:
        video_id = self._extract_video_id(manifest_url)
        filename = folder / (
            f"{video_id}.mp4" if video_id else f"video_{index:03}.mp4"
        )

        if (
            skip_existing
            and filename.exists()
            and filename.stat().st_size > 1024
        ):
            self._log(f"Видео {index}: уже существует", on_log)
            return True, True

        headers = self._manifest_headers.get(
            self._manifest_key(manifest_url),
            {
                "User-Agent": self.USER_AGENT,
                "Referer": "https://yandex.ru/maps/",
                "Origin": "https://yandex.ru",
                "Accept": "*/*",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
        )

        self._log(
            f"Скачиваем свежее видео {index}, пока браузерная сессия активна",
            on_log,
        )
        return (
            self._run_ffmpeg(
                ffmpeg_path,
                manifest_url,
                filename,
                headers,
                on_log,
            ),
            False,
        )

    def collect_and_download(
        self,
        url: str,
        folder: Path | str,
        on_log: LogCallback | None = None,
        skip_existing: bool = True,
        max_items: int = 200,
        no_new_limit: int = 30,
    ) -> tuple[int, int, int, int]:
        """Ищет ролики и скачивает каждый сразу, не закрывая Chromium."""
        self._cancelled = False
        self._manifest_headers = {}
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)

        ffmpeg_path = self._find_ffmpeg()
        if not ffmpeg_path:
            raise RuntimeError(
                "Не найден ffmpeg. Установи ffmpeg или положи ffmpeg.exe рядом с программой."
            )

        self._log(f"Используется ffmpeg: {ffmpeg_path}", on_log)

        pending: list[str] = []
        keys: set[str] = set()
        downloaded_keys: set[str] = set()
        browser: Browser | None = None
        saved = 0
        skipped = 0
        failed = 0

        try:
            with sync_playwright() as playwright:
                self._log("Запуск браузера для поиска видео", on_log)
                browser = playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--autoplay-policy=no-user-gesture-required",
                        "--mute-audio",
                    ],
                )
                self._browser = browser
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=self.USER_AGENT,
                    locale="ru-RU",
                )
                page = context.new_page()
                page.on(
                    "response",
                    lambda response: self._capture_manifest(
                        response,
                        context,
                        pending,
                        keys,
                        on_log,
                    ),
                )

                self._open_gallery(page, url, on_log)
                self._log(
                    "Открываем просмотрщик и обходим материалы галереи",
                    on_log,
                )
                self._open_first_item(page, on_log)

                no_new = 0
                for index in range(max_items):
                    if self._cancelled:
                        break

                    before_found = len(keys)
                    self._play_video(page)
                    page.wait_for_timeout(1200)

                    while pending:
                        manifest_url = pending.pop(0)
                        key = self._manifest_key(manifest_url)
                        if key in downloaded_keys:
                            continue
                        downloaded_keys.add(key)

                        success, was_skipped = self._download_fresh_manifest(
                            ffmpeg_path,
                            manifest_url,
                            folder,
                            len(downloaded_keys),
                            skip_existing,
                            on_log,
                        )
                        if was_skipped:
                            skipped += 1
                        elif success:
                            saved += 1
                        else:
                            failed += 1

                    if len(keys) > before_found:
                        no_new = 0
                    else:
                        no_new += 1

                    if index % 10 == 0:
                        self._log(
                            f"Галерея: материал {index + 1}/{max_items}; "
                            f"найдено: {len(keys)}; скачано: {saved}",
                            on_log,
                        )

                    if no_new >= no_new_limit:
                        self._log(
                            f"Новых видео нет {no_new_limit} материалов подряд, обход завершён",
                            on_log,
                        )
                        break

                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(300)

                page.wait_for_timeout(500)
        finally:
            self._browser = None
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass

        self._log(
            f"Видео найдено: {len(keys)}; сохранено: {saved}; "
            f"пропущено: {skipped}; ошибок: {failed}",
            on_log,
        )
        return len(keys), saved, skipped, failed

    def collect(
        self,
        url: str,
        on_log: LogCallback | None = None,
    ) -> list[str]:
        """Совместимость со старым API. Для импорта используй collect_and_download."""
        manifests: list[str] = []
        keys: set[str] = set()
        self._cancelled = False
        self._manifest_headers = {}
        browser: Browser | None = None

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                self._browser = browser
                context = browser.new_context(user_agent=self.USER_AGENT)
                page = context.new_page()
                page.on(
                    "response",
                    lambda response: self._capture_manifest(
                        response,
                        context,
                        manifests,
                        keys,
                        on_log,
                    ),
                )
                self._open_gallery(page, url, on_log)
                self._open_first_item(page, on_log)
                no_new = 0
                for _ in range(200):
                    if self._cancelled:
                        break
                    before = len(keys)
                    self._play_video(page)
                    page.wait_for_timeout(1200)
                    no_new = 0 if len(keys) > before else no_new + 1
                    if no_new >= 30:
                        break
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(300)
        finally:
            self._browser = None
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass
        return manifests

    def download(
        self,
        urls: list[str],
        folder: Path | str,
        on_log: LogCallback | None = None,
        skip_existing: bool = True,
    ) -> int:
        """Старый режим оставлен для совместимости."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        ffmpeg_path = self._find_ffmpeg()
        if not ffmpeg_path:
            return 0

        saved = 0
        for index, manifest_url in enumerate(urls, start=1):
            success, was_skipped = self._download_fresh_manifest(
                ffmpeg_path,
                manifest_url,
                folder,
                index,
                skip_existing,
                on_log,
            )
            if success and not was_skipped:
                saved += 1
        return saved

    def cancel(self) -> None:
        self._cancelled = True
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
