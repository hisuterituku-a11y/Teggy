import random
import requests
from pathlib import Path

from playwright.sync_api import sync_playwright


class YandexPhotoDownloader:

    def __init__(self, headless=False):
        self.headless = headless
        self.photos = set()


    def log(self, text):
        print(f"[YandexDownloader] {text}")



    def collect(self, url: str):

        self.photos.clear()


        with sync_playwright() as p:


            self.log(
                "Запуск браузера"
            )


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

                    img_url = response.url



                    if (
                        "avatars.mds.yandex.net"
                        not in img_url
                    ):
                        return



                    img_url = img_url.split("?")[0]



                    # убираем только очевидный мусор

                    bad = [

                        "get-vh",
                        "get-maps_stories",
                        "get-yapic",
                        "get-direct",
                        "get-bunker",
                        "get-tycoon",

                    ]



                    if any(
                        x in img_url
                        for x in bad
                    ):
                        return



                    if img_url not in self.photos:

                        self.photos.add(
                            img_url
                        )


                        self.log(
                            f"Фото найдено: {len(self.photos)}"
                        )



                except Exception:

                    pass




            page.on(
                "response",
                handle_response
            )



            # =========================
            # Правильное создание gallery URL
            # =========================

            if "/gallery" in url:

                gallery_url = url


            else:

                base = url.split("?")[0].rstrip("/")

                params = ""

                if "?" in url:

                    params = (
                        "?"
                        +
                        url.split("?", 1)[1]
                    )


                gallery_url = (

                    base
                    +
                    "/gallery/"
                    +
                    params

                )



            self.log(
                f"Открываем галерею: {gallery_url}"
            )



            page.goto(

                gallery_url,

                wait_until="domcontentloaded",

                timeout=60000

            )



            self.log(
                f"LOADED: {page.url}"
            )



            page.wait_for_timeout(
                5000
            )



            self.log(
                "Начинаем плавную прокрутку"
            )



            no_new_counter = 0



            for step in range(300):


                before = len(self.photos)



                # твой рабочий быстрый скролл

                scroll = random.randint(
                    400,
                    800
                )



                page.mouse.wheel(
                    0,
                    scroll
                )



                page.wait_for_timeout(

                    random.randint(
                        700,
                        1300
                    )

                )



                after = len(self.photos)



                if after == before:

                    no_new_counter += 1


                else:

                    no_new_counter = 0



                self.log(

                    f"Шаг {step+1}/300 | "
                    f"Фото: {after}"

                )



                if no_new_counter >= 25:

                    self.log(
                        "Новых фото давно нет. Проверяем конец страницы"
                    )


                    height = page.evaluate(
                        "document.body.scrollHeight"
                    )

                    position = page.evaluate(
                        "window.scrollY + window.innerHeight"
                    )


                    if position >= height - 300:

                        self.log(
                            "Достигнут конец страницы"
                        )

                        break


                    page.wait_for_timeout(
                        3000
                    )


                    no_new_counter = 0




            self.log(

                f"Сбор завершён: {len(self.photos)} фото"

            )



            browser.close()



        return list(self.photos)




    def download(

            self,

            urls,

            folder="yandex_photos"

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



    downloader = YandexPhotoDownloader(

        headless=False

    )



    photos = downloader.collect(
        url
    )



    print()

    print(
        f"Найдено фото: {len(photos)}"
    )



    downloader.download(
        photos
    )



    print()

    print(
        "Готово!"
    )