from __future__ import annotations

import traceback

from PySide6.QtCore import QObject, Signal, Slot

from core.wordstat.tag_generator import TagGenerator


class WordstatWorker(QObject):
    """
    Запускает генерацию тегов в отдельном потоке.

    Внутри никакой UI.
    Только генератор и сигналы.
    """

    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    cancelled = Signal()

    def __init__(self, form_data):
        super().__init__()

        self.form_data = form_data
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    @Slot()
    def run(self):
        try:

            generator = TagGenerator(
                progress_callback=self._progress,
                cancel_callback=self._is_cancelled,
            )

            result = generator.generate(
                service_name=self.form_data.service_name,
                offer_text=self.form_data.offer_text,
                city=self.form_data.city,
                address=self.form_data.address,
                region=self.form_data.region,
                manual_queries=list(self.form_data.manual_queries),
                max_characters=self.form_data.max_characters,
                min_frequency=self.form_data.min_frequency,
                remove_info=self.form_data.remove_info,
                ai_filter=self.form_data.use_ai_filter,
            )

            if self._cancelled:
                self.cancelled.emit()
                return

            self.finished.emit(result)

        except Exception:
            self.error.emit(traceback.format_exc())

    def _progress(self, text: str):
        if not self._cancelled:
            self.progress.emit(text)

    def _is_cancelled(self) -> bool:
        return self._cancelled