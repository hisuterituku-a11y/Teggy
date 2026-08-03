from __future__ import annotations

import traceback

from PySide6.QtCore import QObject, Signal, Slot

from core.wordstat.tag_generator import TagGenerator
from core.wordstat.wordstat_collector import WordstatCollector


class WordstatWorker(QObject):
    """Запускает генерацию тегов Wordstat в отдельном потоке."""

    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    cancelled = Signal()

    def __init__(self, form_data) -> None:
        super().__init__()
        self.form_data = form_data
        self._cancelled = False
        self._collector: WordstatCollector | None = None

    def cancel(self) -> None:
        self._cancelled = True
        collector = self._collector
        if collector is not None:
            # Playwright-контекст создан в рабочем потоке, поэтому закрывать его
            # из GUI-потока нельзя. Достаточно выставить флаг: сборщик проверяет
            # его во всех циклах ожидания и корректно завершает работу сам.
            collector._cancelled = True

    @Slot()
    def run(self) -> None:
        try:
            if self._cancelled:
                self.cancelled.emit()
                return

            collector = WordstatCollector(headless=False)
            self._collector = collector
            generator = TagGenerator(collector=collector)

            result = generator.generate(
                service_name=self.form_data.service_name,
                offer_text=self.form_data.offer_text,
                city=self.form_data.city,
                address=self.form_data.address,
                region=self.form_data.region,
                manual_queries=(
                    list(self.form_data.manual_queries)
                    if self.form_data.manual_queries
                    else None
                ),
                max_characters=self.form_data.max_characters,
                min_frequency=self.form_data.min_frequency,
                remove_info=self.form_data.remove_info,
                use_ai_filter=self.form_data.use_ai_filter,
                continue_on_error=True,
                on_log=self._progress,
            )

            if self._cancelled:
                self.cancelled.emit()
                return

            self.finished.emit(
                {
                    "text": result.text,
                    "collected_count": result.collected_count,
                    "merged_count": result.merged_count,
                    "filtered_count": result.filtered_count,
                    "tag_count": len(result.tags),
                    "character_count": result.character_count,
                    "base_queries": list(result.base_queries),
                }
            )

        except Exception as error:
            if self._cancelled:
                self.cancelled.emit()
                return

            self.error.emit(
                f"{error}\n\n{traceback.format_exc()}"
            )
        finally:
            self._collector = None

    def _progress(self, text: str) -> None:
        if not self._cancelled:
            self.progress.emit(str(text))
