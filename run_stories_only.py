from __future__ import annotations

import sys
from pathlib import Path

from core.yandex.yandex_stories import YandexStoriesDownloader


def log(message: str) -> None:
    print(f"ℹ️ {message}", flush=True)


def main() -> int:
    print("=" * 50)
    print("TEGGY — ТЕСТ ТОЛЬКО STORIES")
    print("=" * 50)

    url = input(
        "Вставьте ссылку на организацию Яндекс Карт:\n> "
    ).strip()

    if not url:
        print("❌ Ссылка не указана")
        return 1

    save_input = input(
        "Папка сохранения Stories "
        "(Enter — ./stories_test):\n> "
    ).strip()

    save_dir = Path(
        save_input or "stories_test"
    ).expanduser().resolve()

    save_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    log(f"Папка сохранения: {save_dir}")
    log("Запускаем только Stories")

    downloader = YandexStoriesDownloader(
        headless=False,
    )

    try:
        urls = downloader.collect(
            url=url,
            on_log=log,
        )

        if not urls:
            log("Stories не найдены")
            return 0

        saved = downloader.download(
            urls=urls,
            folder=save_dir,
            on_log=log,
            skip_existing=True,
        )

        print("=" * 50)
        log(f"Stories найдено: {len(urls)}")
        log(f"Новых файлов сохранено: {saved}")
        log("Тест завершён")
        print("=" * 50)

        return 0

    except KeyboardInterrupt:
        downloader.cancel()
        print("\n⚠️ Операция остановлена пользователем")
        return 130

    except Exception as exc:
        downloader.cancel()
        print(f"\n❌ Ошибка: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
