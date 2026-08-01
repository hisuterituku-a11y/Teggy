from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

from .wordstat_collector import WordstatQuery


LogCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class MergedKeyword:
    """
    Объединённый поисковый запрос.

    phrase:
        Текст поискового запроса.

    frequency:
        Максимальная частотность среди всех найденных вариантов.

    sources:
        Базовые запросы, по которым эта фраза была найдена.
    """

    phrase: str
    frequency: int
    sources: tuple[str, ...] = ()


class KeywordMerger:
    """
    Объединяет результаты нескольких сборов Wordstat.

    Пример входных данных:

    {
        "элайнеры": [...],
        "капы для выравнивания зубов": [...],
        "исправление прикуса": [...],
    }

    Одинаковые фразы объединяются без учёта регистра.
    Для каждой фразы сохраняется максимальная частотность.
    """

    @staticmethod
    def _normalize_phrase(value: str) -> str:
        return " ".join(value.split()).strip(" ,;")

    def merge(
        self,
        batches: Mapping[
            str,
            Iterable[WordstatQuery],
        ],
        on_log: LogCallback | None = None,
    ) -> list[MergedKeyword]:
        """
        Объединяет несколько наборов результатов Wordstat.

        Аргументы:
            batches:
                Словарь вида:

                {
                    "базовый запрос": список WordstatQuery
                }

            on_log:
                Необязательная функция логирования.

        Возвращает:
            Список MergedKeyword, отсортированный
            по убыванию частотности.
        """

        merged: dict[str, dict[str, object]] = {}

        total_received = 0

        for source_query, values in batches.items():
            source_query = self._normalize_phrase(source_query)

            if not source_query:
                continue

            for item in values:
                total_received += 1

                phrase = self._normalize_phrase(item.phrase)

                if not phrase:
                    continue

                if item.frequency <= 0:
                    continue

                key = phrase.casefold()

                existing = merged.get(key)

                if existing is None:
                    merged[key] = {
                        "phrase": phrase,
                        "frequency": item.frequency,
                        "sources": {source_query},
                    }
                    continue

                existing_frequency = int(
                    existing["frequency"]
                )

                if item.frequency > existing_frequency:
                    existing["frequency"] = item.frequency
                    existing["phrase"] = phrase

                sources = existing["sources"]

                if isinstance(sources, set):
                    sources.add(source_query)

        results: list[MergedKeyword] = []

        for value in merged.values():
            sources = value["sources"]

            if isinstance(sources, set):
                normalized_sources = tuple(
                    sorted(
                        sources,
                        key=str.casefold,
                    )
                )
            else:
                normalized_sources = ()

            results.append(
                MergedKeyword(
                    phrase=str(value["phrase"]),
                    frequency=int(value["frequency"]),
                    sources=normalized_sources,
                )
            )

        results.sort(
            key=lambda item: (
                -item.frequency,
                item.phrase.casefold(),
            )
        )

        if on_log:
            on_log(
                "Объединение Wordstat завершено: "
                f"получено {total_received}, "
                f"уникальных {len(results)}"
            )

        return results

    def merge_lists(
        self,
        *batches: Iterable[WordstatQuery],
        on_log: LogCallback | None = None,
    ) -> list[MergedKeyword]:
        """
        Упрощённый вариант для объединения списков,
        когда источник каждого списка не важен.
        """

        mapped_batches = {
            f"source_{index}": batch
            for index, batch in enumerate(
                batches,
                start=1,
            )
        }

        return self.merge(
            batches=mapped_batches,
            on_log=on_log,
        )