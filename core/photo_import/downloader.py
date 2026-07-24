"""
Загрузчик фотографий.

Отвечает только за:
- скачивание файлов
- повторные попытки
- обработку ошибок
- отмену
- обновление PhotoInfo

Не знает про GUI.
"""

from pathlib import Path
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from typing import Callable, List
import threading
import time
import requests

from core.photo_import.models import (
    PhotoInfo,
    ImportStatus
)


class Downloader:
    """
    Многопоточный downloader.
    """

    def __init__(
        self,
        max_workers: int = 5,
        retries: int = 3,
        timeout: int = 30
    ):

        self.max_workers = max_workers
        self.retries = retries
        self.timeout = timeout

        self._cancel_event = threading.Event()



    # ==================================================
    # PUBLIC
    # ==================================================


    def download(
        self,
        photos: List[PhotoInfo],
        save_dir: Path,
        on_progress: Callable = None,
        skip_existing: bool = True
    ) -> List[PhotoInfo]:

        """
        Скачивает список фотографий.

        Всегда возвращает ВСЕ photo objects.
        Даже отменённые.
        """


        if self._cancel_event.is_set():
            for photo in photos:
                photo.status = ImportStatus.CANCELLED

            return photos

        self._cancel_event.clear()


        save_dir.mkdir(
            parents=True,
            exist_ok=True
        )


        results = []


        total = len(photos)

        completed = 0



        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:


            futures = {}


            for photo in photos:


                # уже отменили до старта

                if self._cancel_event.is_set():

                    photo.status = ImportStatus.CANCELLED

                    results.append(photo)

                    continue



                future = executor.submit(

                    self._download_single,

                    photo,

                    save_dir,

                    skip_existing

                )


                futures[future] = photo



            for future in as_completed(futures):


                photo = futures[future]


                try:

                    result = future.result()


                except Exception as e:


                    # железная страховка

                    photo.status = ImportStatus.FAILED

                    photo.error = str(e)

                    result = photo



                results.append(result)



                completed += 1



                if on_progress:

                    on_progress(

                        completed,

                        total,

                        result.filename

                    )



        return results



    # ==================================================
    # SINGLE FILE
    # ==================================================


    def _download_single(
        self,
        photo: PhotoInfo,
        save_dir: Path,
        skip_existing: bool
    ) -> PhotoInfo:



        if self._cancel_event.is_set():

            photo.status = ImportStatus.CANCELLED

            return photo



        try:


            # Фото отзывов складываем отдельно
            if photo.is_review:
                target_dir = save_dir / "отзывы"
            else:
                target_dir = save_dir


            target_dir.mkdir(
                parents=True,
                exist_ok=True
            )


            save_path = (
                target_dir /
                photo.filename
            )



            photo.local_path = save_path



            # -------------------------
            # skip
            # -------------------------

            if (
                skip_existing
                and
                save_path.exists()
            ):

                photo.status = ImportStatus.SKIP

                return photo



            # -------------------------
            # download
            # -------------------------


            photo.status = ImportStatus.DOWNLOADING



            response = self._request_with_retry(
                photo.url
            )



            if response is None:

                photo.status = ImportStatus.FAILED

                photo.error = (
                    "Не удалось получить файл"
                )

                return photo




            # -------------------------
            # save
            # -------------------------


            with open(
                save_path,
                "wb"
            ) as f:

                f.write(
                    response.content
                )



            photo.size = (
                save_path.stat().st_size
            )


            photo.status = ImportStatus.SUCCESS



        except Exception as e:


            photo.status = ImportStatus.FAILED

            photo.error = str(e)



        return photo



    # ==================================================
    # REQUEST WITH RETRY
    # ==================================================


    def _request_with_retry(
        self,
        url: str
    ):


        last_error = None



        for attempt in range(
            1,
            self.retries + 1
        ):



            if self._cancel_event.is_set():

                return None



            try:


                response = requests.get(

                    url,

                    timeout=self.timeout,

                    headers={

                        "User-Agent":
                        (
                            "Mozilla/5.0 "
                            "Chrome/120"
                        )

                    }

                )



                response.raise_for_status()


                return response



            except Exception as e:


                last_error = e



                if attempt < self.retries:

                    time.sleep(
                        attempt
                    )



        return None



    # ==================================================
    # CANCEL
    # ==================================================


    def cancel(self):

        self._cancel_event.set()