from core.photo_import.providers import YandexParser


if __name__ == "__main__":
    # Скрытый режим (по умолчанию)
    parser = YandexParser()  # headless=True
    url = "https://yandex.ru/maps/org/avto_motors/1059724271/gallery/?ll=73.448901%2C61.258090&z=15"
    photos = parser.parse(url, max_photos=5)
    print(f"Найдено фото: {len(photos)}")
    photos = parser.parse(url)
    urls = set(p.url for p in photos)
    print(f"Уникальных URL: {len(urls)}")
    for p in photos[:3]:
        print(p.url)
    parser.close()