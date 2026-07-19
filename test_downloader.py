from pathlib import Path
from core.photo_import.downloader import Downloader
from core.photo_import.models import PhotoInfo, SourceType

# Создаём тестовые PhotoInfo
photos = [
    PhotoInfo(
        url="https://avatars.mds.yandex.net/get-altay/11244149/2a0000018caf6a12527dc4202d20432422e2/XXXL",
        filename="test1.jpg",
        source=SourceType.YANDEX
    ),
    PhotoInfo(
        url="https://avatars.mds.yandex.net/get-altay/10812365/2a0000018a167e085b7f7163537e2aaa1e9f/XXXL",
        filename="test2.jpg",
        source=SourceType.YANDEX
    ),
]

downloader = Downloader(max_workers=2, retries=2)
save_dir = Path("test_downloads")

def on_progress(downloaded, total, filename):
    print(f"Прогресс: {downloaded}/{total} - {filename}")

results = downloader.download(
    photos=photos,
    save_dir=save_dir,
    on_progress=on_progress,
    skip_existing=True
)

for p in results:
    print(f"{p.filename}: {p.status} - {p.local_path}")