from pathlib import Path

from PIL import Image
import imagehash


class PhotoComparator:

    def __init__(
            self,
            org_folder="yandex_photos",
            reviews_folder="reviews_photos"
    ):

        self.org_folder = Path(org_folder)
        self.reviews_folder = Path(reviews_folder)

        self.report = []



    def log(self, text):

        print(f"[PhotoCompare] {text}")



    def get_hash(self, file):

        try:

            img = Image.open(file)

            img = img.convert("RGB")

            return imagehash.phash(img)

        except Exception as e:

            self.log(
                f"Ошибка хеша {file.name}: {e}"
            )

            return None



    def scan_folder(self, folder):

        result = {}

        if not folder.exists():

            self.log(
                f"Папка не найдена: {folder}"
            )

            return result



        files = list(folder.glob("*"))

        self.log(
            f"Сканируем {folder}: {len(files)} файлов"
        )



        for file in files:

            if file.suffix.lower() not in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            ]:
                continue



            h = self.get_hash(file)

            if h:

                result[file] = h



        return result



    def compare(self):

        self.log(
            "Начинаем сравнение"
        )



        org = self.scan_folder(
            self.org_folder
        )

        reviews = self.scan_folder(
            self.reviews_folder
        )



        if not org:

            self.log(
                "Нет фото организации для сравнения"
            )
            return



        if not reviews:

            self.log(
                "Нет фото отзывов"
            )
            return



        duplicates = 0



        report_file = Path(
            "duplicates_report.txt"
        )



        for review_file, review_hash in reviews.items():

            for org_file, org_hash in org.items():

                difference = (
                    review_hash - org_hash
                )



                if difference <= 5:

                    self.log(
                        "Дубликат:"
                        f"\n  Отзывы: {review_file.name}"
                        f"\n  Организация: {org_file.name}"
                        f"\n  Сходство hash: {difference}"
                    )



                    self.report.append(
                        f"""
Дубликат

Отзывы:
{review_file}

Организация:
{org_file}

Hash difference:
{difference}

-----------------------
"""
                    )



                    try:

                        org_file.unlink()

                        self.log(
                            f"Удалён дубль из организации: {org_file.name}"
                        )

                    except Exception as e:

                        self.log(
                            f"Ошибка удаления {org_file.name}: {e}"
                        )



                    duplicates += 1

                    break



        report_file.write_text(
            "\n".join(self.report),
            encoding="utf-8"
        )



        self.log(
            f"Готово. Дубликатов найдено: {duplicates}"
        )

        self.log(
            f"Отчёт: {report_file}"
        )

        self.log(
            "В папке yandex_photos остались только уникальные фото организации"
        )

        self.log(
            "В папке reviews_photos остались все фото отзывов"
        )



if __name__ == "__main__":

    comparator = PhotoComparator(

        org_folder="yandex_photos",

        reviews_folder="reviews_photos"

    )

    comparator.compare()

    print()

    print("Завершено!")