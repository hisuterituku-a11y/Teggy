from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from threading import Lock
from typing import Callable
from urllib.parse import urlsplit

from playwright.sync_api import Browser, sync_playwright


LogCallback = Callable[[str], None]


class YandexVideoDownloader:
    """Собирает и скачивает видео организации из Яндекс Карт."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30,
    ) -> None:
        self.headless = headless
        self.timeout = timeout

        self._cancelled = False
        self._browser: Browser | None = None
        self._process: subprocess.Popen[str] | None = None
        self._process_lock = Lock()

    def _log(
        self,
        text: str,
        on_log: LogCallback | None = None,
    ) -> None:
        if on_log:
            on_log(text)
        else:
            print(f"[Video] {text}")

    @staticmethod
    def _is_video_url(url: str) -> bool:
        clean_url = url.split("?", 1)[0].lower()
        return clean_url.endswith((".m3u8", ".mp4", ".webm"))

    @staticmethod
    def _video_key(url: str) -> str:
        parsed = urlsplit(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def collect(
        self,
        url: str,
        on_log: LogCallback | None = None,
        max_wait_seconds: float = 180.0,
        stall_threshold: float = 12.0,
    ) -> list[str]:
        browser: Browser | None = None
        found: dict[str, str] = {}

        def register(candidate: str) -> None:
            if not self._is_video_url(candidate):
                return

            key = self._video_key(candidate)
            if key in found:
                return

            found[key] = candidate
            self._log(f"Видео найдено: {len(found)}", on_log)

        try:
            with sync_playwright() as playwright:
                self._log("Открываем Яндекс Карты для поиска видео", on_log)
                browser = playwright.chromium.launch(headless=self.headless)
                self._browser = browser

                context = browser.new_context(
                    viewport={"width": 1400, "height": 900},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120 Safari/537.36"
                    ),
                )
                page = context.new_page()

                def response_handler(response) -> None:
                    if self._cancelled:
                        return
                    try:
                        register(response.url)
                    except Exception:
                        return

                page.on("response", response_handler)
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout * 1000,
                )
                page.wait_for_timeout(4000)

                started_at = time.monotonic()
                last_growth_at = started_at
                last_count = 0

                while not self._cancelled:
                    now = time.monotonic()
                    if now - started_at >= max_wait_seconds:
                        self._log("Достигнут общий тайм-аут поиска видео", on_log)
                        break

                    page.mouse.wheel(0, 1200)
                    page.wait_for_timeout(1000)

                    current_count = len(found)
                    if current_count > last_count:
                        last_count = current_count
                        last_growth_at = time.monotonic()
                        continue

                    if time.monotonic() - last_growth_at >= stall_threshold:
                        self._log("Новых видео больше не появляется", on_log)
                        break

                if self._cancelled:
                    self._log("Поиск видео отменён", on_log)

        finally:
            self._browser = None
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass

        result = list(found.values())
        self._log(f"Видео найдено всего: {len(result)}", on_log)
        return result

    @staticmethod
    def _ffmpeg_path() -> str:
        path = shutil.which("ffmpeg")
        if path is None:
            raise RuntimeError(
                "ffmpeg не найден. Установите ffmpeg и добавьте его в PATH"
            )
        return path

    def _stop_process(self) -> None:
        with self._process_lock:
            process = self._process

        if process is None or process.poll() is not None:
            return

        try:
            process.terminate()
            process.wait(timeout=3)
        except Exception:
            try:
                process.kill()
                process.wait(timeout=3)
            except Exception:
                pass

    def _download_manifest(
        self,
        url: str,
        target: Path,
        on_log: LogCallback | None = None,
        startup_timeout: float = 45.0,
        no_progress_timeout: float = 90.0,
        max_runtime: float = 1800.0,
    ) -> bool:
        ffmpeg = self._ffmpeg_path()
        temp_path = target.with_suffix(target.suffix + ".part")
        temp_path.unlink(missing_ok=True)

        command = [
            ffmpeg,
            "-y",
            "-nostdin",
            "-loglevel",
            "error",
            "-i",
            url,
            "-c",
            "copy",
            str(temp_path),
        ]

        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
        )

        with self._process_lock:
            self._process = process

        started_at = time.monotonic()
        last_growth_at = started_at
        previous_size = 0

        try:
            while process.poll() is None:
                if self._cancelled:
                    self._log("Останавливаем ffmpeg", on_log)
                    self._stop_process()
                    return False

                now = time.monotonic()
                size = temp_path.stat().st_size if temp_path.exists() else 0

                if size > previous_size:
                    previous_size = size
                    last_growth_at = now

                if size == 0 and now - started_at >= startup_timeout:
                    self._log("ffmpeg не начал запись вовремя", on_log)
                    self._stop_process()
                    return False

                if size > 0 and now - last_growth_at >= no_progress_timeout:
                    self._log("ffmpeg перестал записывать данные", on_log)
                    self._stop_process()
                    return False

                if now - started_at >= max_runtime:
                    self._log("Превышено максимальное время загрузки видео", on_log)
                    self._stop_process()
                    return False

                time.sleep(0.25)

            if process.returncode != 0:
                stderr = process.stderr.read().strip() if process.stderr else ""
                message = stderr[-1000:] if stderr else "неизвестная ошибка ffmpeg"
                self._log(f"ffmpeg завершился с ошибкой: {message}", on_log)
                return False

            if not temp_path.exists() or temp_path.stat().st_size == 0:
                self._log("ffmpeg не создал файл видео", on_log)
                return False

            temp_path.replace(target)
            return True

        finally:
            with self._process_lock:
                if self._process is process:
                    self._process = None

            if temp_path.exists() and not target.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def download(
        self,
        urls: list[str],
        folder: Path | str,
        on_log: LogCallback | None = None,
        skip_existing: bool = True,
    ) -> int:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)

        if urls:
            self._ffmpeg_path()

        saved = 0
        skipped = 0
        total = len(urls)

        for index, url in enumerate(urls, start=1):
            if self._cancelled:
                self._log("Скачивание видео отменено", on_log)
                break

            target = folder / f"video_{index:03}.mp4"
            if skip_existing and target.exists() and target.stat().st_size > 0:
                skipped += 1
                self._log(f"Видео {index}/{total}: уже существует", on_log)
                continue

            self._log(f"Скачивание видео {index}/{total}", on_log)
            try:
                if self._download_manifest(url, target, on_log):
                    saved += 1
                    self._log(f"Видео скачано: {index}/{total}", on_log)
                elif self._cancelled:
                    break
                else:
                    self._log(f"Видео {index}/{total} не сохранено", on_log)
            except Exception as exc:
                self._log(f"Ошибка скачивания видео {index}: {exc}", on_log)

        self._log(
            f"Видео сохранено: {saved}; пропущено существующих: {skipped}",
            on_log,
        )
        return saved

    def cancel(self) -> None:
        self._cancelled = True
        self._stop_process()

        browser = self._browser
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
