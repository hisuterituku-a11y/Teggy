from core.yandex.yandex_stories import YandexStoriesDownloader


url = input(
    "Ссылка организации:\n> "
).strip()


downloader = YandexStoriesDownloader(
    headless=False
)


stories = downloader.collect(
    url,
    on_log=print
)


print("\n====================")
print("ИТОГО:", len(stories))
print("====================")


for s in stories:
    print(s)