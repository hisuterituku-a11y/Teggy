import time
import random
import requests
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


class YandexReviewDownloader:

    def __init__(self, headless=False):
        self.headless = headless
        self.photos = set()


    def log(self, text):
        print(f"[YandexReviews] {text}")


    def collect(self, url: str):

        self.photos.clear()


        with sync_playwright() as p:

            self.log("Запуск браузера")


            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                ]
            )


            context = browser.new_context(
                viewport={
                    "width": 1920,
                    "height": 1080
                },
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120 Safari/537.36"
                )
            )


            page = context.new_page()



            def handle_response(response):

                try:

                    url = response.url


                    if (
                        "avatars.mds.yandex.net"
                        not in url
                    ):
                        return


                    url = url.split("?")[0]
                    # просим максимальное качество Яндекса
                    sizes = [
                        "/S",
                        "/M",
                        "/L",
                        "/XL",
                        "/XXL",
                        "/XXXL"
                    ]

                    for size in sizes:
                        if url.endswith(size):
                            url = url[:-len(size)] + "/XXXL"
                            break


                    # только фото отзывов
                    bad = [
                        "get-vh",
                        "get-maps_stories",
                        "get-yapic",
                        "get-direct",
                        "get-bunker",
                        "get-tycoon",
                    ]


                    if any(
                        x in url
                        for x in bad
                    ):
                        return



                    if url not in self.photos:

                        self.photos.add(url)

                        self.log(
                            f"Фото найдено: {len(self.photos)}"
                        )


                except Exception:
                    pass



            page.on(
                "response",
                handle_response
            )



            # нормализуем ссылку отзывов

            base = url.split("?")[0].rstrip("/")

            params = ""

            if "?" in url:
                params = "?" + url.split("?", 1)[1]


            if base.endswith("/reviews"):

                reviews_url = (
                    base
                    +
                    "/"
                    +
                    params
                )

            else:

                reviews_url = (
                    base
                    +
                    "/reviews/"
                    +
                    params
                )


            self.log(
                f"Открываем отзывы: {reviews_url}"
            )



            page.goto(
                reviews_url,
                wait_until="domcontentloaded",
                timeout=60000
            )



            page.wait_for_timeout(
                5000
            )



            self.log(
                "Начинаем плавную прокрутку отзывов"
            )



            no_new_counter = 0



            

            for step in range(300):

                before = len(self.photos)

                scroll = random.randint(
                    700,
                    1200
                )

                page.mouse.wheel(
                    0,
                    scroll
                )

                page.wait_for_timeout(
                    random.randint(
                        300,
                        700
                    )
                )

                after = len(self.photos)


                if after == before:
                    no_new_counter += 1
                else:
                    no_new_counter = 0


                self.log(
                    f"Шаг {step+1}/300 | "
                    f"Фото отзывов: {after}"
                )


                # стоп после 20 пустых шагов
                if no_new_counter >= 10:

                    self.log(
                        "Проверка финальной догрузки..."
                    )

                    page.wait_for_timeout(
                        5000
                    )

                    if len(self.photos) == after:
                        break

                    no_new_counter = 0




            self.log(
                f"Сбор отзывов завершён: {len(self.photos)} фото"
            )


            browser.close()



        return list(self.photos)



    def save_json(
            self,
            urls,
            filename="reviews_urls.json"
    ):

        Path(filename).write_text(
            json.dumps(
                urls,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )


        self.log(
            f"Ссылки сохранены: {filename}"
        )



    def download(
            self,
            urls,
            folder="reviews_photos"
    ):


        folder = Path(folder)

        folder.mkdir(
            exist_ok=True
        )



        session = requests.Session()



        total = len(urls)



        for i, url in enumerate(urls, 1):

            try:


                filename = (
                    folder
                    /
                    f"{i:03}.jpg"
                )



                r = session.get(
                    url,
                    headers={
                        "User-Agent":
                        "Mozilla/5.0"
                    },
                    timeout=30
                )


                r.raise_for_status()



                filename.write_bytes(
                    r.content
                )



                self.log(
                    f"Скачано {i}/{total}"
                )



            except Exception as e:

                self.log(
                    f"Ошибка скачивания {i}: {e}"
                )




if __name__ == "__main__":


    url = input(
        "\nСсылка Яндекс организации:\n> "
    ).strip()



    downloader = YandexReviewDownloader(
        headless=False
    )



    photos = downloader.collect(
        url
    )



    print()

    print(
        f"Найдено фото отзывов: {len(photos)}"
    )



    downloader.save_json(
        photos
    )



    downloader.download(
        photos
    )



    print()

    print(
        "Готово!"
    )