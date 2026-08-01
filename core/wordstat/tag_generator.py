from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .keyword_filter import KeywordFilter
from .keyword_merger import KeywordMerger, MergedKeyword
from .tag_optimizer import OptimizedTags, TagOptimizer
from .wordstat_collector import WordstatCollector


LogCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class TagGenerationResult:
    """
    Полный результат генерации тегов.

    optimized:
        Готовая строка тегов и служебная информация.

    base_queries:
        Базовые запросы, отправленные в Wordstat.

    collected_count:
        Общее количество запросов, полученных из Wordstat.

    merged_count:
        Количество уникальных запросов после объединения.

    filtered_count:
        Количество запросов после фильтрации.
    """

    optimized: OptimizedTags
    base_queries: tuple[str, ...]
    collected_count: int
    merged_count: int
    filtered_count: int

    @property
    def text(self) -> str:
        return self.optimized.text

    @property
    def tags(self) -> tuple[str, ...]:
        return self.optimized.tags

    @property
    def character_count(self) -> int:
        return self.optimized.character_count


class TagGenerator:
    """
    Полный конвейер генерации тегов:

    1. Определение базовых запросов.
    2. Сбор Wordstat.
    3. Объединение результатов.
    4. Фильтрация.
    5. Укладка в лимит символов.

    KeywordExpander и AIKeywordFilter необязательны.
    Пока OpenAI не подключён, генератор работает без них.
    """

    def __init__(
        self,
        collector: WordstatCollector,
        *,
        expander=None,
        merger: KeywordMerger | None = None,
        rule_filter: KeywordFilter | None = None,
        ai_filter=None,
        optimizer: TagOptimizer | None = None,
    ) -> None:
        self.collector = collector
        self.expander = expander
        self.merger = merger or KeywordMerger()
        self.rule_filter = rule_filter or KeywordFilter()
        self.ai_filter = ai_filter
        self.optimizer = optimizer or TagOptimizer(
            max_characters=3000,
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(str(value).split()).strip(" ,;\n\t")

    def _prepare_base_queries(
        self,
        *,
        service_name: str,
        city: str,
        address: str,
        manual_queries: Iterable[str] | None,
        on_log: LogCallback | None,
    ) -> list[str]:
        """
        Формирует список запросов для Wordstat.

        Приоритет:

        1. manual_queries, если они переданы;
        2. KeywordExpander, если он подключён;
        3. только service_name.
        """

        raw_queries: list[str]

        if manual_queries is not None:
            raw_queries = list(manual_queries)

            if on_log:
                on_log(
                    "Используются вручную заданные "
                    "базовые запросы"
                )

        elif self.expander is not None:
            if on_log:
                on_log(
                    "Формирование базовых запросов "
                    "с помощью AI"
                )

            raw_queries = self.expander.expand(
                service_name=service_name,
                city=city,
                address=address,
                on_log=on_log,
            )

        else:
            raw_queries = [service_name]

            if on_log:
                on_log(
                    "AI-расширение не подключено. "
                    "Используется название услуги"
                )

        result: list[str] = []
        seen: set[str] = set()

        # Название услуги всегда должно присутствовать.
        for raw_query in [service_name, *raw_queries]:
            query = self._normalize(raw_query)

            if not query:
                continue

            key = query.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(query)

        return result

    def _collect_batches(
        self,
        *,
        base_queries: list[str],
        region: str,
        on_log: LogCallback | None,
        continue_on_error: bool,
    ) -> tuple[dict[str, list], int]:
        """
        Собирает Wordstat для каждого базового запроса.
        """

        batches: dict[str, list] = {}
        collected_count = 0

        for index, query in enumerate(
            base_queries,
            start=1,
        ):
            if on_log:
                on_log(
                    f"Wordstat {index}/{len(base_queries)}: "
                    f"{query}"
                )

            try:
                items = self.collector.collect(
                    query=query,
                    region=region,
                    on_log=on_log,
                )
            except TypeError:
                # На случай, если текущий collector.collect()
                # пока не принимает on_log.
                try:
                    items = self.collector.collect(
                        query=query,
                        region=region,
                    )
                except Exception as error:
                    if not continue_on_error:
                        raise

                    if on_log:
                        on_log(
                            f"Ошибка сбора запроса "
                            f"'{query}': {error}"
                        )

                    items = []

            except Exception as error:
                if not continue_on_error:
                    raise

                if on_log:
                    on_log(
                        f"Ошибка сбора запроса "
                        f"'{query}': {error}"
                    )

                items = []

            batch = list(items or [])
            batches[query] = batch
            collected_count += len(batch)

            if on_log:
                on_log(
                    f"Для запроса '{query}' "
                    f"получено: {len(batch)}"
                )

        return batches, collected_count

    def generate(
        self,
        *,
        service_name: str,
        region: str,
        city: str = "",
        address: str = "",
        manual_queries: Iterable[str] | None = None,
        max_characters: int = 3000,
        min_frequency: int = 1,
        remove_info: bool = False,
        use_ai_filter: bool = True,
        continue_on_error: bool = True,
        on_log: LogCallback | None = None,
    ) -> TagGenerationResult:
        """
        Запускает полный процесс генерации тегов.

        service_name:
            Название услуги.

        region:
            Регион Wordstat.

        manual_queries:
            Необязательный список базовых запросов.
            Пока AI не подключён, сюда можно передать
            несколько запросов вручную.

        use_ai_filter:
            Использовать AI-фильтрацию, если она подключена.

        continue_on_error:
            Продолжать работу, если один запрос Wordstat
            завершился ошибкой.
        """

        service_name = self._normalize(service_name)
        region = self._normalize(region)
        city = self._normalize(city)
        address = self._normalize(address)

        if not service_name:
            raise ValueError(
                "Не указано название услуги"
            )

        if not region:
            raise ValueError(
                "Не указан регион Wordstat"
            )

        if max_characters < 1:
            raise ValueError(
                "Лимит символов должен быть больше нуля"
            )

        if on_log:
            on_log(
                f"Запуск генерации тегов: "
                f"{service_name}"
            )

        # 1. Базовые запросы
        base_queries = self._prepare_base_queries(
            service_name=service_name,
            city=city,
            address=address,
            manual_queries=manual_queries,
            on_log=on_log,
        )

        if not base_queries:
            raise RuntimeError(
                "Не удалось сформировать "
                "базовые запросы"
            )

        if on_log:
            on_log(
                "Базовые запросы: "
                + ", ".join(base_queries)
            )

        # 2. Wordstat
        batches, collected_count = (
            self._collect_batches(
                base_queries=base_queries,
                region=region,
                on_log=on_log,
                continue_on_error=continue_on_error,
            )
        )

        if collected_count == 0:
            if on_log:
                on_log(
                    "Wordstat не вернул запросов"
                )

            empty_result = self.optimizer.optimize(
                [],
                service_name=service_name,
                city=city,
                address=address,
                max_characters=max_characters,
                on_log=on_log,
            )

            return TagGenerationResult(
                optimized=empty_result,
                base_queries=tuple(base_queries),
                collected_count=0,
                merged_count=0,
                filtered_count=0,
            )

        # 3. Объединение
        merged = self.merger.merge(
            batches=batches,
            on_log=on_log,
        )

        # 4. Обычная фильтрация
        filtered: list[MergedKeyword] = (
            self.rule_filter.filter(
                merged,
                remove_info=remove_info,
                min_frequency=min_frequency,
                on_log=on_log,
            )
        )

        # 5. AI-фильтрация, когда появится AI-клиент
        if use_ai_filter and self.ai_filter is not None:
            if on_log:
                on_log(
                    "Запуск второго уровня "
                    "AI-фильтрации"
                )

            filtered = self.rule_filter.filter(
                merged,
                city=city,
                remove_info=remove_info,
                min_frequency=min_frequency,
                on_log=on_log,
            )

        elif use_ai_filter and on_log:
            on_log(
                "AI-фильтр не подключён, "
                "этап пропущен"
            )

        # 6. Итоговые 3000 символов
        optimized = self.optimizer.optimize(
            filtered,
            service_name=service_name,
            city=city,
            address=address,
            max_characters=max_characters,
            on_log=on_log,
        )

        if on_log:
            on_log(
                "Генерация завершена: "
                f"{optimized.character_count}/"
                f"{max_characters} символов"
            )

        return TagGenerationResult(
            optimized=optimized,
            base_queries=tuple(base_queries),
            collected_count=collected_count,
            merged_count=len(merged),
            filtered_count=len(filtered),
        )
    