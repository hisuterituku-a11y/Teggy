from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urlsplit, urlunsplit
from playwright.sync_api import Browser, Page, sync_playwright


LogCallback = Callable[[str], None]


class YandexVideoDownloader:
    """
    Сбор и скачивание видео из карточки организации Яндекс Карт.

    Сборщик сохраняет только DASH-манифесты manifest.mpd.
    Отдельные изображения, init-фрагменты и .m4s-фрагменты игнорируются.
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 60,
    ) -> None:
        self.headless = headless
        self.timeout = timeout

        self._cancelled = False
        self._browser: Browser | None = None

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
        """
        Извлекает ID вида vplxxxxxxxxxxxxxxxxxxxx.

        Примеры:
        /vod-content/vplv7w3wge47jiwfkvwu/
        video=vplv7w3wge47jiwfkvwu
        /player/vplv7w3wge47jiwfkvwu.json
        """
        decoded_url = unquote(url)

        match = re.search(
            r"\b(vpl[a-zA-Z0-9_-]+)\b",
            decoded_url,
        )

        if not match:
            return None

        return match.group(1)

    @staticmethod
    def _is_manifest_response(
        url: str,
        content_type: str,
    ) -> bool:
        """
        Принимает только полноценные DASH/HLS-манифесты.

        Не принимает:
        - JPEG/WebP-обложки get-vh;
        - init-v1.mp4;
        - init-a1.mp4;
        - fragment-*.m4s;
        - отдельные video/mp4 и audio/mp4 сегменты.
        """
        lower_url = url.lower()
        lower_content_type = content_type.lower()

        if "manifest.mpd" in lower_url:
            return True

        if lower_url.endswith(".mpd"):
            return True

        if ".mpd?" in lower_url:
            return True

        if "application/dash+xml" in lower_content_type:
            return True

        if ".m3u8" in lower_url:
            return True

        if "mpegurl" in lower_content_type:
            return True

        return False

    @staticmethod
    def _manifest_key(url: str) -> str:
        """
        Создаёт ключ для удаления дублей.

        Один ролик может несколько раз открываться с разными:
        - vsid;
        - vpuid;
        - t;
        - серверами strm.

        Поэтому основной ключ — ID видео vpl...
        """
        video_id = YandexVideoDownloader._extract_video_id(url)

        if video_id:
            return video_id

        return url.split("?", 1)[0]

    def _register_manifest(
        self,
        url: str,
        content_type: str,
        manifests: list[str],
        manifest_keys: set[str],
        on_log: LogCallback | None,
    ) -> None:
        if not self._is_manifest_response(
            url,
            content_type,
        ):
            return

        key = self._manifest_key(url)

        if key in manifest_keys:
            return

        manifest_keys.add(key)
        manifests.append(url)

        video_id = self._extract_video_id(url)

        if video_id:
            self._log(
                f"Видео найдено: {len(manifests)} ({video_id})",
                on_log,
            )
        else:
            self._log(
                f"Видео найдено: {len(manifests)}",
                on_log,
            )
    @staticmethod
    def _make_gallery_url(url: str) -> str:
        """
        Возвращает нормальную ссылку на галерею организации.

        Поддерживает:
        - ссылку на карточку организации;
        - ссылку на галерею;
        - ссылку на конкретный материал галереи;
        - ссылки с параметрами ll, z, photos и другими.
        """
        parts = urlsplit(url)

        path = parts.path.rstrip("/")

        if "/gallery" in path:
            path = path.split("/gallery", 1)[0]

        gallery_path = path + "/gallery/"

        return urlunsplit(
            (
                parts.scheme or "https",
                parts.netloc or "yandex.ru",
                gallery_path,
                parts.query,
                "",
            )
        )
    def _open_gallery(
        self,
        page: Page,
        organization_url: str,
        on_log: LogCallback | None,
    ) -> str:
        gallery_url = self._make_gallery_url(
            organization_url
        )

        self._log(
            f"Открываем галерею: {gallery_url}",
            on_log,
        )

        page.goto(
            gallery_url,
            wait_until="domcontentloaded",
            timeout=self.timeout * 1000,
        )

        page.wait_for_timeout(5000)

        if "/gallery/" not in page.url:
            self._log(
                "Яндекс вывел из галереи, открываем её повторно",
                on_log,
            )

            page.goto(
                gallery_url,
                wait_until="domcontentloaded",
                timeout=self.timeout * 1000,
            )

            page.wait_for_timeout(5000)

        self._log(
            f"Текущая страница: {page.url}",
            on_log,
        )

        return gallery_url

    def _find_video_candidates(
        self,
        page: Page,
    ) -> list:
        """
        Ищет элементы галереи, которые похожи на видео.

        Яндекс регулярно меняет CSS-классы, потому используются:
        - элементы с SVG-иконкой play;
        - ссылки с video/vpl в href;
        - элементы с video в class/data/aria-label;
        - карточки, содержащие play-иконку.
        """
        selectors = (
            "a[href*='photos'][href*='vpl']",
            "a[href*='video']",
            "[data-id*='vpl']",
            "[data-photo-id*='vpl']",
            "[data-video-id]",
            "[class*='video']",
            "[aria-label*='видео' i]",
            "[aria-label*='video' i]",
            "svg[class*='play']",
            "use[href*='play']",
            "use[xlink\\:href*='play']",
        )

        candidates = []
        seen_elements: set[str] = set()

        for selector in selectors:
            try:
                locator = page.locator(selector)
                count = locator.count()

                for index in range(count):
                    element = locator.nth(index)

                    try:
                        signature = element.evaluate(
                            """
                            element => {
                                const target =
                                    element.closest(
                                        'a, button, [role="button"], div'
                                    ) || element;

                                return [
                                    target.tagName,
                                    target.getAttribute('href') || '',
                                    target.getAttribute('class') || '',
                                    target.getAttribute('data-id') || '',
                                    target.getAttribute('data-photo-id') || '',
                                    target.getAttribute('aria-label') || '',
                                    target.textContent || ''
                                ].join('|');
                            }
                            """
                        )

                        if signature in seen_elements:
                            continue

                        seen_elements.add(signature)
                        candidates.append(element)

                    except Exception:
                        continue

            except Exception:
                continue

        return candidates

    def _click_video_candidates(
        self,
        page: Page,
        manifests: list[str],
        on_log: LogCallback | None,
    ) -> None:
        candidates = self._find_video_candidates(page)

        self._log(
            f"Кандидатов на видео найдено: {len(candidates)}",
            on_log,
        )

        last_manifest_count = len(manifests)
        failed_clicks = 0

        for index, element in enumerate(
            candidates,
            start=1,
        ):
            if self._cancelled:
                return

            try:
                clickable = element.locator(
                    "xpath=ancestor-or-self::*["
                    "self::a or "
                    "self::button or "
                    "@role='button'"
                    "][1]"
                )

                if clickable.count() > 0:
                    target = clickable.first
                else:
                    target = element

                target.scroll_into_view_if_needed(
                    timeout=3000,
                )

                page.wait_for_timeout(250)

                target.click(
                    force=True,
                    timeout=3000,
                )

                page.wait_for_timeout(2500)

                try:
                    video = page.locator("video").last

                    if video.count() > 0:
                        video.evaluate(
                            """
                            video => {
                                video.muted = true;
                                const result = video.play();

                                if (result && result.catch) {
                                    result.catch(() => {});
                                }
                            }
                            """
                        )

                        page.wait_for_timeout(1800)

                except Exception:
                    pass

                if len(manifests) > last_manifest_count:
                    self._log(
                        (
                            f"Обработан кандидат {index}/"
                            f"{len(candidates)}; "
                            f"видео: {len(manifests)}"
                        ),
                        on_log,
                    )

                    last_manifest_count = len(manifests)
                    failed_clicks = 0
                else:
                    failed_clicks += 1

                try:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(400)
                except Exception:
                    pass

                if failed_clicks >= 30:
                    self._log(
                        "Новых видео давно нет, завершаем проверку",
                        on_log,
                    )
                    break

            except Exception:
                failed_clicks += 1
                continue

    def _open_video_links_from_gallery(
        self,
        page: Page,
        manifests: list[str],
        on_log: LogCallback | None,
    ) -> None:
        """
        Дополнительно собирает ссылки, содержащие ID vpl,
        и открывает их по очереди.
        """
        try:
            links = page.locator(
                "a[href*='photos'][href*='vpl']"
            )

            hrefs: list[str] = []
            seen_hrefs: set[str] = set()

            for index in range(links.count()):
                try:
                    href = links.nth(index).get_attribute("href")

                    if not href:
                        continue

                    if href in seen_hrefs:
                        continue

                    seen_hrefs.add(href)
                    hrefs.append(href)

                except Exception:
                    continue

            self._log(
                f"Прямых ссылок на видео: {len(hrefs)}",
                on_log,
            )

            for index, href in enumerate(
                hrefs,
                start=1,
            ):
                if self._cancelled:
                    return

                try:
                    page.goto(
                        href,
                        wait_until="domcontentloaded",
                        timeout=self.timeout * 1000,
                    )

                    page.wait_for_timeout(2500)

                    try:
                        video = page.locator("video").last

                        if video.count() > 0:
                            video.evaluate(
                                """
                                video => {
                                    video.muted = true;
                                    const result = video.play();

                                    if (result && result.catch) {
                                        result.catch(() => {});
                                    }
                                }
                                """
                            )

                            page.wait_for_timeout(1800)

                    except Exception:
                        pass

                    self._log(
                        (
                            f"Ссылка на видео {index}/"
                            f"{len(hrefs)}; "
                            f"найдено: {len(manifests)}"
                        ),
                        on_log,
                    )

                except Exception:
                    continue

        except Exception:
            return
    def _scroll_gallery(
        self,
        page: Page,
        on_log: LogCallback | None,
    ) -> None:
        """
        Прокручивает галерею, чтобы Яндекс подгрузил больше материалов.
        """
        self._log(
            "Прокручиваем галерею для загрузки всех материалов",
            on_log,
        )

        previous_height = 0
        unchanged_steps = 0

        for step in range(120):
            if self._cancelled:
                return

            try:
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(350)

                current_height = page.evaluate(
                    """
                    () => Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    )
                    """
                )

                if current_height == previous_height:
                    unchanged_steps += 1
                else:
                    previous_height = current_height
                    unchanged_steps = 0

                if step % 10 == 0:
                    self._log(
                        f"Галерея: шаг {step + 1}/120",
                        on_log,
                    )

                if unchanged_steps >= 15:
                    break

            except Exception as error:
                self._log(
                    f"Ошибка прокрутки галереи: {error}",
                    on_log,
                )
                break

    def _play_current_video(
        self,
        page: Page,
    ) -> None:
        """Запускает текущее видео, если открытый материал является видео."""
        try:
            videos = page.locator("video")

            if videos.count() == 0:
                return

            video = videos.last
            video.evaluate(
                """
                video => {
                    video.muted = true;
                    video.autoplay = true;
                    const result = video.play();

                    if (result && result.catch) {
                        result.catch(() => {});
                    }
                }
                """
            )
        except Exception:
            return

    def _current_material_signature(
        self,
        page: Page,
    ) -> str:
        """Возвращает приблизительный идентификатор открытого материала."""
        try:
            return page.evaluate(
                """
                () => {
                    const visible = element => {
                        const rect = element.getBoundingClientRect();
                        const style = getComputedStyle(element);

                        return (
                            rect.width > 250 &&
                            rect.height > 250 &&
                            style.visibility !== 'hidden' &&
                            style.display !== 'none' &&
                            Number(style.opacity || 1) > 0
                        );
                    };

                    const media = [
                        ...document.querySelectorAll('video, img')
                    ].filter(visible);

                    media.sort((a, b) => {
                        const ar = a.getBoundingClientRect();
                        const br = b.getBoundingClientRect();
                        return (br.width * br.height) - (ar.width * ar.height);
                    });

                    const element = media[0];

                    if (!element) {
                        return location.href;
                    }

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
        except Exception:
            return page.url

    def _open_first_gallery_item(
        self,
        page: Page,
        on_log: LogCallback | None,
    ) -> None:
        """Открывает первый видимый материал галереи."""
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
                count = min(locator.count(), 30)

                for index in range(count):
                    element = locator.nth(index)

                    try:
                        if not element.is_visible():
                            continue

                        box = element.bounding_box()

                        if not box:
                            continue

                        if box["width"] < 80 or box["height"] < 80:
                            continue

                        element.scroll_into_view_if_needed(timeout=3000)
                        element.click(force=True, timeout=3000)
                        page.wait_for_timeout(1200)

                        self._log(
                            f"Первый материал открыт через: {selector}",
                            on_log,
                        )
                        return
                    except Exception:
                        continue
            except Exception:
                continue

        raise RuntimeError(
            "Не удалось открыть первый материал галереи"
        )

    def _walk_gallery(
        self,
        page: Page,
        manifests: list[str],
        on_log: LogCallback | None,
        max_items: int = 150,
    ) -> None:
        """
        Открывает просмотрщик и проходит материалы клавишей ArrowRight.

        Фото пропускаются. У видео запускается воспроизведение, после чего
        обработчик response перехватывает manifest.mpd.
        """
        self._log(
            "Открываем просмотрщик и обходим материалы галереи",
            on_log,
        )

        self._open_first_gallery_item(
            page,
            on_log,
        )

        seen_signatures: set[str] = set()
        repeated = 0

        for index in range(max_items):
            if self._cancelled:
                return

            before_count = len(manifests)

            self._play_current_video(page)
            page.wait_for_timeout(1800)

            signature = self._current_material_signature(page)

            if signature in seen_signatures:
                repeated += 1
            else:
                seen_signatures.add(signature)
                repeated = 0

            if index % 10 == 0:
                self._log(
                    (
                        f"Галерея: материал {index + 1}/{max_items}; "
                        f"видео найдено: {len(manifests)}"
                    ),
                    on_log,
                )

            if len(manifests) > before_count:
                self._log(
                    f"Новый manifest перехвачен; всего: {len(manifests)}",
                    on_log,
                )

            if repeated >= 3:
                self._log(
                    "Материалы начали повторяться, обход завершён",
                    on_log,
                )
                break

            try:
                page.keyboard.press("ArrowRight")
                page.wait_for_timeout(500)
            except Exception as error:
                self._log(
                    f"Не удалось перейти к следующему материалу: {error}",
                    on_log,
                )
                break

    def collect(
        self,
        url: str,
        on_log: LogCallback | None = None,
    ) -> list[str]:
        self._cancelled = False

        manifests: list[str] = []
        manifest_keys: set[str] = set()

        browser: Browser | None = None

        try:
            with sync_playwright() as playwright:
                self._log(
                    "Запуск браузера для поиска видео",
                    on_log,
                )

                browser = playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features="
                        "AutomationControlled",
                        "--autoplay-policy="
                        "no-user-gesture-required",
                        "--mute-audio",
                    ],
                )

                self._browser = browser

                context = browser.new_context(
                    viewport={
                        "width": 1920,
                        "height": 1080,
                    },
                    user_agent=(
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                )

                page = context.new_page()

                def handle_response(response) -> None:
                    if self._cancelled:
                        return

                    try:
                        content_type = response.headers.get(
                            "content-type",
                            "",
                        )

                        self._register_manifest(
                            url=response.url,
                            content_type=content_type,
                            manifests=manifests,
                            manifest_keys=manifest_keys,
                            on_log=on_log,
                        )

                    except Exception:
                        return

                page.on(
                    "response",
                    handle_response,
                )
                gallery_url = self._open_gallery(
                    page,
                    url,
                    on_log,
                )

                if self._cancelled:
                    return manifests

                self._walk_gallery(
                    page,
                    manifests,
                    on_log,
                    max_items=150,
                )

                page.wait_for_timeout(2000)

        except Exception as error:
            self._log(
                f"Ошибка при сборе видео: {error}",
                on_log,
            )

        finally:
            self._browser = None

            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass

        self._log(
            f"Сбор видео завершён: {len(manifests)}",
            on_log,
        )

        return manifests

    @staticmethod
    def _find_ffmpeg() -> str | None:
        """
        Ищет ffmpeg:
        1. в PATH;
        2. рядом с приложением;
        3. в папке bin рядом с приложением.
        """
        system_ffmpeg = shutil.which("ffmpeg")

        if system_ffmpeg:
            return system_ffmpeg

        local_candidates = (
            Path("ffmpeg.exe"),
            Path("bin") / "ffmpeg.exe",
            Path("tools") / "ffmpeg.exe",
            Path("ffmpeg") / "bin" / "ffmpeg.exe",
        )

        for candidate in local_candidates:
            if candidate.exists():
                return str(candidate.resolve())

        return None

    def _download_manifest(
        self,
        ffmpeg_path: str,
        manifest_url: str,
        filename: Path,
        on_log: LogCallback | None,
    ) -> bool:
        import time

        temp_path = filename.with_name(
            f"{filename.stem}.part{filename.suffix}"
        )

        command = [
            ffmpeg_path,
            "-y",
            "-nostdin",
            "-loglevel",
            "error",
            "-rw_timeout",
            "15000000",
            "-headers",
            (
                "Referer: https://yandex.ru/maps/\r\n"
                "Origin: https://yandex.ru\r\n"
                "User-Agent: Mozilla/5.0\r\n"
            ),
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

        creation_flags = (
            subprocess.CREATE_NO_WINDOW
            if hasattr(subprocess, "CREATE_NO_WINDOW")
            else 0
        )

        error_filename = filename.with_suffix(
            filename.suffix + ".ffmpeg.log"
        )

        error_filename.unlink(missing_ok=True)
        temp_path.unlink(missing_ok=True)

        process: subprocess.Popen | None = None

        startup_timeout = 30
        no_progress_timeout = 45
        maximum_download_time = 600

        started_at = time.monotonic()
        last_progress_at = started_at
        last_size = 0

        try:
            with error_filename.open(
                "w",
                encoding="utf-8",
                errors="replace",
            ) as error_file:


                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=error_file,
                    creationflags=creation_flags,
                )



                while process.poll() is None:
                    if self._cancelled:
                        self._log(
                            "Скачивание видео отменено",
                            on_log,
                        )
                        break

                    now = time.monotonic()

                    try:
                        current_size = (
                            temp_path.stat().st_size
                            if temp_path.exists()
                            else 0
                        )
                    except OSError:
                        current_size = 0

                    if current_size > last_size:
                        last_size = current_size
                        last_progress_at = now


                    elapsed = now - started_at
                    no_progress_elapsed = now - last_progress_at

                    if (
                        current_size == 0
                        and elapsed >= startup_timeout
                    ):
                        self._log(
                            (
                                "ffmpeg за 30 секунд не начал "
                                "получать данные"
                            ),
                            on_log,
                        )
                        break

                    if (
                        current_size > 0
                        and no_progress_elapsed >= no_progress_timeout
                    ):
                        self._log(
                            (
                                "Размер файла не меняется "
                                "45 секунд"
                            ),
                            on_log,
                        )
                        break

                    if elapsed >= maximum_download_time:
                        self._log(
                            (
                                "Превышено максимальное время "
                                "загрузки: 600 секунд"
                            ),
                            on_log,
                        )
                        break

                    time.sleep(0.2)

                if process.poll() is None:
                    process.terminate()

                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()

                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            pass

            return_code = process.returncode

            if return_code != 0:
                try:
                    error_text = error_filename.read_text(
                        encoding="utf-8",
                        errors="replace",
                    ).strip()
                except OSError:
                    error_text = ""

                if error_text:
                    self._log(
                        f"Ошибка ffmpeg: {error_text[-3000:]}",
                        on_log,
                    )
                else:
                    self._log(
                        (
                            "ffmpeg завершился с ошибкой, "
                            f"код: {return_code}"
                        ),
                        on_log,
                    )

                temp_path.unlink(missing_ok=True)
                return False

            if not temp_path.exists():
                self._log(
                    "ffmpeg не создал временный файл",
                    on_log,
                )
                return False

            file_size = temp_path.stat().st_size

            if file_size < 1024:
                self._log(
                    "Итоговый файл слишком маленький",
                    on_log,
                )

                temp_path.unlink(missing_ok=True)
                return False

            temp_path.replace(filename)

            self._log(
                (
                    "Видео сохранено: "
                    f"{file_size / 1024 / 1024:.2f} МБ"
                ),
                on_log,
            )

            return True

        except Exception as error:
            if process is not None and process.poll() is None:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except Exception:
                    pass

            temp_path.unlink(missing_ok=True)

            self._log(
                f"Ошибка запуска ffmpeg: {error}",
                on_log,
            )

            return False

        finally:
            error_filename.unlink(missing_ok=True)

    def download(
        self,
        urls: list[str],
        folder: Path | str,
        on_log: LogCallback | None = None,
        skip_existing: bool = True,
    ) -> int:
        folder = Path(folder)

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not urls:
            self._log(
                "Видео для скачивания не найдено",
                on_log,
            )
            return 0

        ffmpeg_path = self._find_ffmpeg()

        if not ffmpeg_path:
            self._log(
                (
                    "Не найден ffmpeg. Установи ffmpeg "
                    "или положи ffmpeg.exe в папку "
                    "с программой."
                ),
                on_log,
            )
            return 0

        self._log(
            f"Используется ffmpeg: {ffmpeg_path}",
            on_log,
        )

        saved = 0
        skipped = 0
        total = len(urls)

        download_urls = list(reversed(urls))

        for index, manifest_url in enumerate(
            download_urls,
            start=1,
        ):
            if self._cancelled:
                self._log(
                    "Скачивание видео отменено",
                    on_log,
                )
                break

            video_id = self._extract_video_id(
                manifest_url,
            )

            if video_id:
                filename = folder / f"{video_id}.mp4"
            else:
                filename = (
                    folder
                    / f"video_{index:03}.mp4"
                )

            if (
                skip_existing
                and filename.exists()
                and filename.stat().st_size > 1024
            ):
                skipped += 1

                self._log(
                    (
                        f"Видео {index}/{total}: "
                        f"уже существует"
                    ),
                    on_log,
                )
                continue

            self._log(
                f"Скачивание видео {index}/{total}",
                on_log,
            )

            success = self._download_manifest(
                ffmpeg_path=ffmpeg_path,
                manifest_url=manifest_url,
                filename=filename,
                on_log=on_log,
            )

            if not success:
                self._log(
                    (
                        f"Видео {index}/{total}: "
                        f"не удалось скачать"
                    ),
                    on_log,
                )
                continue

            saved += 1

            self._log(
                f"Видео скачано: {index}/{total}",
                on_log,
            )

        self._log(
            (
                f"Видео сохранено: {saved}; "
                f"пропущено существующих: {skipped}"
            ),
            on_log,
        )

        return saved

    def cancel(self) -> None:
        self._cancelled = True

        browser = self._browser

        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass