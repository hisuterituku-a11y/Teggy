import sys
from pathlib import Path

# добавляем корень проекта
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


from core.photo_import.providers import YandexParser
from core.photo_import.downloader import Downloader


URL = (
    "https://yandex.ru/maps/org/meditsinskiy_tsentr_raduga_zdorovya/"
    "236501266119/gallery/"
)


SAVE_DIR = Path("test_download")


if __name__ == "__main__":

    print("=" * 60)
    print("TEST YANDEX IMPORT")
    print("=" * 60)


    parser = YandexParser(
        headless=False
    )


    try:

        photos = parser.parse(
            URL
        )


        print()
        print(
            f"Найдено фото: {len(photos)}"
        )


        for p in photos[:10]:

            print(
                p.filename,
                "|",
                p.url[:80]
            )


        if not photos:
            print("ФОТО НЕ НАЙДЕНЫ")
            exit()



        print()
        print("Начинаем загрузку...")


        downloader = Downloader(
            max_workers=5,
            retries=3
        )


        result = downloader.download(
            photos,
            SAVE_DIR
        )


        print()
        print("=" * 60)

        success = sum(
            1
            for p in result
            if p.status.value == "success"
        )

        failed = sum(
            1
            for p in result
            if p.status.value == "failed"
        )


        print(
            f"Успешно: {success}"
        )

        print(
            f"Ошибок: {failed}"
        )

        print(
            f"Папка: {SAVE_DIR.absolute()}"
        )


    finally:

        parser.close()