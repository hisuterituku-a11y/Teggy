"""
Worker для фонового импорта фотографий.

Работает внутри QThread.

Отвечает только за:
- запуск процесса
- связь Service <-> GUI
- прогресс
- ошибки
- отмену

Не выбирает источник.
Не создаёт Downloader.
Не управляет потоками.
"""

from PySide6.QtCore import QObject, Signal

from core.photo_import.models import (
    ImportProgress,
    ImportTask,
    ImportStatus,
)

from core.photo_import.exceptions import (
    CancelledError,
)


class ImportWorker(QObject):
    """
    Фоновый worker импорта.
    """

    progress = Signal(ImportProgress)
    log = Signal(str)
    finished = Signal()
    error = Signal(str)


    def __init__(
        self,
        task: ImportTask,
        callbacks: dict,
        parser,
        downloader
    ):

        super().__init__()

        self.task = task

        self.callbacks = callbacks or {}

        self.parser = parser

        self.downloader = downloader

        self._is_cancelled = False


        # callback'и для тестов и прямого использования
        self._on_progress_callback = (
            self.callbacks.get("on_progress")
        )

        self._on_log_callback = (
            self.callbacks.get("on_log")
        )


        self._on_error_callback = (
            self.callbacks.get("on_error")
        )



    # ==================================================
    # RUN
    # ==================================================

    def run(self):

        try:

            self._log(
                f"Начинаем импорт: {self.task.source_url}"
            )


            self._check_cancelled()


            # -------------------------
            # PARSE
            # -------------------------

            self.task.status = ImportStatus.PARSING


            self._notify_progress(
                "Парсинг страницы..."
            )


            try:

                photos = self.parser.parse(
                    self.task.source_url
                )

            finally:

                try:
                    self.parser.close()
                except Exception:
                    pass



            self._check_cancelled()



            if not photos:

                self.task.status = ImportStatus.FAILED


                self._log(
                    "Фотографии не найдены"
                )


                self._notify_progress(
                    "Фотографии не найдены"
                )


                return



            self._log(
                f"Найдено фотографий: {len(photos)}"
            )


            self.task.photos = photos

            self.task.total = len(photos)



            # -------------------------
            # DOWNLOAD
            # -------------------------

            self.task.status = ImportStatus.DOWNLOADING


            self._notify_progress(
                f"Скачивание {self.task.total} файлов..."
            )



            def download_progress(
                downloaded,
                total,
                filename
            ):

                self.task.downloaded = downloaded


                self._notify_progress(
                    f"Скачано {downloaded}/{total}",
                    filename
                )



            results = self.downloader.download(

                photos=photos,

                save_dir=self.task.save_dir,

                on_progress=download_progress,

                skip_existing=
                    self.callbacks.get(
                        "skip_existing",
                        True
                    )
            )



            # -------------------------
            # RESULT
            # -------------------------


            self.task.photos = results


            self.task.downloaded = sum(
                1
                for p in results
                if p.status == ImportStatus.SUCCESS
            )


            self.task.failed = sum(
                1
                for p in results
                if p.status == ImportStatus.FAILED
            )


            self.task.skipped = sum(
                1
                for p in results
                if p.status == ImportStatus.SKIP
            )


            cancelled = any(
                p.status == ImportStatus.CANCELLED
                for p in results
            )



            if cancelled:

                self.task.status = ImportStatus.CANCELLED

                self._log(
                    "Импорт отменён"
                )


            else:

                self.task.status = ImportStatus.SUCCESS


                self._log(

                    "Импорт завершён: "

                    f"скачано {self.task.downloaded}, "

                    f"пропущено {self.task.skipped}, "

                    f"ошибок {self.task.failed}"

                )



            self._notify_progress(
                "Готово"
            )



        except CancelledError:

            self.task.status = ImportStatus.CANCELLED


            self._log(
                "Импорт отменён пользователем"
            )


            self._notify_progress(
                "Импорт отменён"
            )



        except Exception as e:


            self.task.status = ImportStatus.FAILED


            message = (
                f"Ошибка импорта: {e}"
            )


            self._log(message)


            self._emit_error(
                str(e)
            )



        finally:

            self.finished.emit()



    # ==================================================
    # PROGRESS
    # ==================================================

    def _notify_progress(
        self,
        message: str,
        current_file: str = ""
    ):


        percent = 0


        if self.task.total:

            percent = (

                (
                    self.task.downloaded
                    +
                    self.task.failed
                    +
                    self.task.skipped
                )

                /

                self.task.total

            ) * 100



        progress = ImportProgress(

            task_id=self.task.id,

            total=self.task.total,

            downloaded=self.task.downloaded,

            failed=self.task.failed,

            skipped=self.task.skipped,

            current_file=current_file,

            percent=min(percent, 100),

            status=self.task.status,

            message=message

        )


        self._emit_progress(progress)



    def _emit_progress(
        self,
        progress: ImportProgress
    ):

        self.progress.emit(progress)


        if self._on_progress_callback:

            try:

                self._on_progress_callback(
                    progress
                )

            except Exception:
                pass



    # ==================================================
    # LOG / ERROR
    # ==================================================

    def _log(
        self,
        message: str
    ):

        self.log.emit(message)


        if self._on_log_callback:

            try:

                self._on_log_callback(
                    message
                )

            except Exception:
                pass



    def _emit_error(
        self,
        message: str
    ):

        self.error.emit(message)


        if self._on_error_callback:

            try:

                self._on_error_callback(
                    message
                )

            except Exception:
                pass



    # ==================================================
    # HELPERS
    # ==================================================

    def _check_cancelled(self):

        if self._is_cancelled:

            raise CancelledError(
                "Отменено пользователем"
            )



    # ==================================================
    # CANCEL
    # ==================================================

    def cancel(self):

        self._is_cancelled = True


        if self.parser:

            try:

                self.parser.cancel()

            except Exception:
                pass



        if self.downloader:

            try:

                self.downloader.cancel()

            except Exception:
                pass