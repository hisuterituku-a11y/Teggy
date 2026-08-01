from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

import requests


HEADERS = {
    "Referer": "https://yandex.ru/maps/",
    "Origin": "https://yandex.ru",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def download(url: str, destination: Path) -> None:
    print(f"\nGET {url}")

    with requests.get(
        url,
        headers=HEADERS,
        timeout=60,
        stream=True,
    ) as response:
        print("HTTP:", response.status_code)
        print("Content-Type:", response.headers.get("content-type"))
        print("Content-Length:", response.headers.get("content-length"))

        response.raise_for_status()

        with destination.open("wb") as file:
            for chunk in response.iter_content(1024 * 256):
                if chunk:
                    file.write(chunk)

    print(f"Сохранено: {destination}")
    print(f"Размер: {destination.stat().st_size} байт")


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Использование:\n"
            "python test_manifest_segments.py путь_к_manifest.mpd"
        )
        return 1

    manifest_path = Path(sys.argv[1]).resolve()

    if not manifest_path.is_file():
        print(f"Файл не найден: {manifest_path}")
        return 1

    root = ET.parse(manifest_path).getroot()
    namespace = {"mpd": "urn:mpeg:dash:schema:mpd:2011"}

    base_urls = [
        element.text.strip()
        for element in root.findall("mpd:BaseURL", namespace)
        if element.text
    ]

    if not base_urls:
        print("В manifest не найден BaseURL")
        return 1

    # Берём первое представление видео, обычно оно максимального качества.
    video_adaptation = None

    for adaptation in root.findall(
        ".//mpd:AdaptationSet",
        namespace,
    ):
        content_type = adaptation.get("contentType", "")
        mime_type = adaptation.get("mimeType", "")

        if content_type == "video" or mime_type.startswith("video/"):
            video_adaptation = adaptation
            break

    if video_adaptation is None:
        print("В manifest не найдена видеодорожка")
        return 1

    representation = video_adaptation.find(
        "mpd:Representation",
        namespace,
    )

    if representation is None:
        print("Видеопредставление не найдено")
        return 1

    template = representation.find(
        "mpd:SegmentTemplate",
        namespace,
    )

    if template is None:
        template = video_adaptation.find(
            "mpd:SegmentTemplate",
            namespace,
        )

    if template is None:
        print("SegmentTemplate не найден")
        return 1

    initialization = template.get("initialization")
    media = template.get("media")
    start_number = int(template.get("startNumber", "1"))

    if not initialization or not media:
        print("В SegmentTemplate нет initialization или media")
        return 1

    fragment = media.replace("$Number$", str(start_number))

    output_dir = manifest_path.parent / "manifest_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("BaseURL вариантов:", len(base_urls))
    print("Representation:", representation.attrib)
    print("Папка результата:", output_dir)

    errors: list[str] = []

    for index, base_url in enumerate(base_urls, start=1):
        print(f"\n=== Сервер {index}/{len(base_urls)} ===")
        print(base_url)

        init_url = urljoin(base_url, initialization)
        fragment_url = urljoin(base_url, fragment)

        try:
            download(
                init_url,
                output_dir / f"server_{index}_init.mp4",
            )
            download(
                fragment_url,
                output_dir / f"server_{index}_fragment_1.m4s",
            )

            print("\nТЕСТ УСПЕШЕН")
            print("Python скачал init и первый фрагмент.")
            return 0

        except Exception as exc:
            message = f"Сервер {index}: {type(exc).__name__}: {exc}"
            errors.append(message)
            print("ОШИБКА:", message)

    print("\nВсе BaseURL завершились ошибкой:")
    for error in errors:
        print("-", error)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())