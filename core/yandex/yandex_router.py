from __future__ import annotations

from pathlib import Path
from typing import Any

from core.yandex.diagnostics import (
    format_exception_report,
    save_diagnostic_report,
)

from core.yandex.photo_compare import PhotoComparator
from core.yandex.yandex_downloader import YandexPhotoDownloader
from core.yandex.yandex_reviews import YandexReviewDownloader
from core.yandex.yandex_stories import YandexStoriesDownloader


class YandexRouter:
    """Последовательно запускает загрузчики Яндекс Карт."""

    def __init__(self) -> None:
        self._cancelled = False
        self._active_downloader: Any | None = None
        self._log_lines: list[str] = []
        self._save_dir: Path | None = None
        self._base_url: str | None = None

    def log(self, text: str) -> None:
        line = str(text)
        self._log_lines.append(line)
        print(f"[YandexRouter] {line}")

    def progress(self, text: str) -> None:
        print(f"[YandexRouter:progress] {text}")

    @staticmethod
    def _normalize_base_url(url: str) -> str:
        clean_url = url.strip()

        if not clean_url:
            raise ValueError("Не указана ссылка на организацию")

        return (
            clean_url
            .split("/gallery", 1)[0]
            .split("/reviews", 1)[0]
            .split("?", 1)[0]
            .rstrip("/")
        )

    def _check_cancelled(self) -> bool:
        if not self._cancelled:
            return False

        self.log("Операция отменена пользователем")
        return True

    def _set_active_downloader(
        self,
        downloader: Any | None,
    ) -> None:
        self._active_downloader = downloader

        if self._cancelled and downloader is not None:
            try:
                downloader.cancel()
            except Exception:
                pass

    def _download_organization_photos(
        self,
        gallery_url: str,
        folder: Path,
        skip_existing: bool,
    ) -> int:
        self.progress("Фото организации")
        self.log("================================")
        self.log("ЭТАП 1: ФОТО ОРГАНИЗАЦИИ")
        self.log(f"Открываем: {gallery_url}")

        downloader = YandexPhotoDownloader(
            headless=False,
        )
        self._set_active_downloader(downloader)

        try:
            urls = downloader.collect(
                gallery_url,
                on_log=self.log,
            )

            if self._check_cancelled():
                return 0

            saved = downloader.download(
                urls,
                folder=folder,
                on_log=self.log,
                skip_existing=skip_existing,
            )

            self.log(
                (
                    f"Фото организации найдено: {len(urls)}; "
                    f"сохранено новых: {saved}"
                )
            )

            return len(urls)

        finally:
            self._set_active_downloader(None)

    def _download_review_photos(
        self,
        reviews_url: str,
        folder: Path,
        skip_existing: bool,
    ) -> int:
        self.progress("Фото отзывов")
        self.log("================================")
        self.log("ЭТАП 2: ФОТО ОТЗЫВОВ")
        self.log(f"Открываем: {reviews_url}")

        downloader = YandexReviewDownloader(
            headless=False,
        )
        self._set_active_downloader(downloader)

        try:
            urls = downloader.collect(
                reviews_url,
                on_log=self.log,
            )

            if self._check_cancelled():
                return 0

            saved = downloader.download(
                urls,
                folder=folder,
                on_log=self.log,
                skip_existing=skip_existing,
            )

            self.log(
                (
                    f"Фото отзывов найдено: {len(urls)}; "
                    f"сохранено новых: {saved}"
                )
            )

            return len(urls)

        finally:
            self._set_active_downloader(None)

    def _compare_photos(
        self,
        org_folder: Path,
        reviews_folder: Path,
    ) -> None:
        self.progress("Удаление дублей")
        self.log("================================")
        self.log("ЭТАП 3: СРАВНЕНИЕ ФОТО")
        self.log(
            "Сравниваем фото организации и фото отзывов"
        )

        comparator = PhotoComparator(
            org_folder=org_folder,
            reviews_folder=reviews_folder,
        )
        comparator.compare()

        self.log(
            "Сравнение завершено, дубли удалены из папки организации"
        )

    def _download_stories(
        self,
        base_url: str,
        folder: Path,
        skip_existing: bool,
    ) -> int:
        self.progress("Stories")
        self.log("================================")
        self.log("ЭТАП 4: STORIES")

        downloader = YandexStoriesDownloader(
            headless=True,
        )
        self._set_active_downloader(downloader)

        try:
            urls = downloader.collect(
                base_url,
                on_log=self.log,
            )

            if self._check_cancelled():
                return 0

            if not urls:
                self.log(
                    "Stories не найдены — продолжаем без ошибки"
                )
                return 0

            saved = downloader.download(
                urls,
                folder=folder,
                on_log=self.log,
                skip_existing=skip_existing,
            )

            self.log(
                (
                    f"Stories найдено: {len(urls)}; "
                    f"сохранено новых: {saved}"
                )
            )

            return len(urls)

        finally:
            self._set_active_downloader(None)

    def _register_error(
        self,
        *,
        stage: str,
        exc: BaseException,
        url: str | None = None,
    ) -> str:
        """Пишет подробную ошибку в лог и сохраняет диагностику."""
        report = format_exception_report(
            stage=stage,
            exc=exc,
            url=url,
        )

        for line in report.splitlines():
            self.log(line)

        if self._save_dir is not None:
            try:
                diagnostic_dir = save_diagnostic_report(
                    save_dir=self._save_dir,
                    stage=stage,
                    exc=exc,
                    url=url,
                    log_lines=self._log_lines,
                )
                self.log(
                    f"[ERROR] Диагностика сохранена: {diagnostic_dir}"
                )
            except Exception as diagnostic_exc:
                self.log(
                    "[ERROR] Не удалось сохранить диагностику: "
                    f"{diagnostic_exc}"
                )

        return (
            f"{stage}: {type(exc).__name__}: {exc}"
        )

    def run(
        self,
        url: str,
        save_dir: Path | str,
        skip_existing: bool = True,
    ) -> bool:
        self._cancelled = False
        self._log_lines = []

        save_dir = Path(save_dir)
        self._save_dir = save_dir
        save_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        base_url = self._normalize_base_url(url)
        self._base_url = base_url
        gallery_url = f"{base_url}/gallery/"
        reviews_url = f"{base_url}/reviews/"

        org_folder = save_dir / "Фото организации"
        reviews_folder = save_dir / "Фото отзывы"
        stories_folder = save_dir / "Сторис"

        org_folder.mkdir(
            parents=True,
            exist_ok=True,
        )
        reviews_folder.mkdir(
            parents=True,
            exist_ok=True,
        )
        stories_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log("================================")
        self.log("ЗАПУСК ИМПОРТА ИЗ ЯНДЕКС КАРТ")
        self.log(f"Организация: {base_url}")
        self.log(f"Папка сохранения: {save_dir}")

        org_count = 0
        reviews_count = 0
        stories_count = 0

        errors: list[str] = []

        try:
            org_count = self._download_organization_photos(
                gallery_url=gallery_url,
                folder=org_folder,
                skip_existing=skip_existing,
            )
        except Exception as exc:
            message = self._register_error(
                stage="Фото организации",
                exc=exc,
                url=gallery_url,
            )
            errors.append(message)

        if self._check_cancelled():
            return False

        try:
            reviews_count = self._download_review_photos(
                reviews_url=reviews_url,
                folder=reviews_folder,
                skip_existing=skip_existing,
            )
        except Exception as exc:
            message = self._register_error(
                stage="Фото отзывов",
                exc=exc,
                url=reviews_url,
            )
            errors.append(message)

        if self._check_cancelled():
            return False

        try:
            self._compare_photos(
                org_folder=org_folder,
                reviews_folder=reviews_folder,
            )
        except Exception as exc:
            message = self._register_error(
                stage="Сравнение фотографий",
                exc=exc,
                url=base_url,
            )
            errors.append(message)

        if self._check_cancelled():
            return False

        try:
            stories_count = self._download_stories(
                base_url=base_url,
                folder=stories_folder,
                skip_existing=skip_existing,
            )
        except Exception as exc:
            message = self._register_error(
                stage="Stories",
                exc=exc,
                url=base_url,
            )
            errors.append(message)
            self.log(
                "Ошибка Stories не прерывает импорт остальных фотографий"
            )

        if self._check_cancelled():
            return False

        self.progress("Готово")
        self.log("================================")
        self.log("ГОТОВО")
        self.log(f"Организация: {org_count} фото")
        self.log(f"Отзывы: {reviews_count} фото")
        self.log(f"Stories: {stories_count}")

        if errors:
            self.log(
                f"Завершено с предупреждениями: {len(errors)}"
            )

            for error in errors:
                self.log(f"• {error}")
        else:
            self.log("Все этапы завершены без ошибок")

        self.log("================================")

        return True

    def cancel(self) -> None:
        self._cancelled = True

        downloader = self._active_downloader

        if downloader is not None:
            try:
                downloader.cancel()
            except Exception:
                pass
