from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .keyword_filter import KeywordFilter
from .keyword_matrix_builder import KeywordExpansion
from .keyword_merger import KeywordMerger, MergedKeyword
from .tag_optimizer import OptimizedTags, TagOptimizer
from .wordstat_collector import WordstatCollector


LogCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class TagGenerationResult:
    """Полный результат генерации тегов."""

    optimized: OptimizedTags
    base_queries: tuple[str, ...]
    collected_count: int
    merged_count: int
    filtered_count: int
    generated_count: int = 0
    expansion: KeywordExpansion | None = None

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

    1. Анализ предложения и определение базовых запросов.
    2. Сбор Wordstat.
    3. Объединение результатов.
    4. Детерминированная фильтрация.
    5. Необязательная AI-фильтрация.
    6. Добавление контролируемых фраз из матрицы предложения.
    7. Укладка результата в лимит символов.
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
        expansion: KeywordExpansion | None,
        on_log: LogCallback | None,
    ) -> list[str]:
        raw_queries: list[str]

        if manual_queries is not None:
            raw_queries = list(manual_queries)
            if on_log:
                on_log("Используются вручную заданные базовые запросы")

        elif expansion is not None:
            raw_queries = list(expansion.seed_queries)
            if on_log:
                on_log(
                    "Используются базовые запросы из анализа предложения"
                )

        elif self.expander is not None:
            if on_log:
                on_log("Формирование базовых запросов с помощью AI")

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

    def _expand_offer(
        self,
        *,
        offer_text: str,
        service_name: str,
        city: str,
        address: str,
        on_log: LogCallback | None,
    ) -> KeywordExpansion | None:
        if not offer_text or self.expander is None:
            return None

        expand_offer = getattr(self.expander, "expand_offer", None)
        if not callable(expand_offer):
            if on_log:
                on_log(
                    "Структурный анализ предложения не поддерживается "
                    "текущим расширителем"
                )
            return None

        if on_log:
            on_log("Запускаем структурный анализ предложения")

        return expand_offer(
            offer_text=offer_text,
            service_name=service_name,
            city=city,
            address=address,
            on_log=on_log,
        )

    def _collect_batches(
        self,
        *,
        base_queries: list[str],
        region: str,
        on_log: LogCallback | None,
        continue_on_error: bool,
    ) -> tuple[dict[str, list], int]:
        batches: dict[str, list] = {}
        collected_count = 0

        for index, query in enumerate(base_queries, start=1):
            if on_log:
                on_log(
                    f"Wordstat {index}/{len(base_queries)}: {query}"
                )

            try:
                items = self.collector.collect(
                    query=query,
                    region=region,
                    on_log=on_log,
                )
            except TypeError:
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
                            f"Ошибка сбора запроса '{query}': {error}"
                        )
                    items = []
            except Exception as error:
                if not continue_on_error:
                    raise
                if on_log:
                    on_log(
                        f"Ошибка сбора запроса '{query}': {error}"
                    )
                items = []

            batch = list(items or [])
            batches[query] = batch
            collected_count += len(batch)

            if on_log:
                on_log(
                    f"Для запроса '{query}' получено: {len(batch)}"
                )

        return batches, collected_count

    @staticmethod
    def _combine_generated_keywords(
        filtered: list[MergedKeyword],
        expansion: KeywordExpansion | None,
    ) -> tuple[list[MergedKeyword], int]:
        if expansion is None:
            return filtered, 0

        combined: dict[str, MergedKeyword] = {
            item.phrase.casefold(): item
            for item in filtered
        }
        added = 0

        for item in expansion.generated_keywords:
            key = item.phrase.casefold()
            if key in combined:
                continue

            # Синтетическая частотность не подменяет Wordstat. Она нужна только,
            # чтобы локальная фраза прошла общую структуру ранжирования.
            combined[key] = MergedKeyword(
                phrase=item.phrase,
                frequency=1,
                sources=(f"generated:{item.cluster}",),
            )
            added += 1

        return list(combined.values()), added

    def generate(
        self,
        *,
        service_name: str,
        region: str,
        city: str = "",
        address: str = "",
        offer_text: str = "",
        manual_queries: Iterable[str] | None = None,
        max_characters: int = 3000,
        min_frequency: int = 1,
        remove_info: bool = False,
        use_ai_filter: bool = True,
        continue_on_error: bool = True,
        include_generated_keywords: bool = True,
        on_log: LogCallback | None = None,
    ) -> TagGenerationResult:
        service_name = self._normalize(service_name)
        region = self._normalize(region)
        city = self._normalize(city)
        address = self._normalize(address)
        offer_text = self._normalize(offer_text)

        if not service_name:
            raise ValueError("Не указано название услуги")
        if not region:
            raise ValueError("Не указан регион Wordstat")
        if max_characters < 1:
            raise ValueError("Лимит символов должен быть больше нуля")

        if on_log:
            on_log(f"Запуск генерации тегов: {service_name}")

        expansion = self._expand_offer(
            offer_text=offer_text,
            service_name=service_name,
            city=city,
            address=address,
            on_log=on_log,
        )

        base_queries = self._prepare_base_queries(
            service_name=service_name,
            city=city,
            address=address,
            manual_queries=manual_queries,
            expansion=expansion,
            on_log=on_log,
        )

        if not base_queries:
            raise RuntimeError("Не удалось сформировать базовые запросы")

        if on_log:
            on_log("Базовые запросы: " + ", ".join(base_queries))

        batches, collected_count = self._collect_batches(
            base_queries=base_queries,
            region=region,
            on_log=on_log,
            continue_on_error=continue_on_error,
        )

        merged = self.merger.merge(
            batches=batches,
            on_log=on_log,
        ) if collected_count else []

        filtered: list[MergedKeyword] = self.rule_filter.filter(
            merged,
            city=city,
            remove_info=remove_info,
            min_frequency=min_frequency,
            on_log=on_log,
        )

        if use_ai_filter and self.ai_filter is not None:
            if on_log:
                on_log("Запуск второго уровня AI-фильтрации")

            filtered = self.ai_filter.filter(
                filtered,
                service_name=service_name,
                city=city,
                address=address,
                on_log=on_log,
            )
        elif use_ai_filter and on_log:
            on_log("AI-фильтр не подключён, этап пропущен")

        generated_count = 0
        optimization_source = filtered

        if include_generated_keywords:
            optimization_source, generated_count = (
                self._combine_generated_keywords(
                    filtered,
                    expansion,
                )
            )
            if on_log and generated_count:
                on_log(
                    "Добавлено локальных и коммерческих фраз из матрицы: "
                    f"{generated_count}"
                )

        if not optimization_source and on_log:
            on_log("Wordstat и матрица не вернули подходящих запросов")

        optimized = self.optimizer.optimize(
            optimization_source,
            service_name=service_name,
            city=city,
            address=address,
            max_characters=max_characters,
            on_log=on_log,
        )

        if on_log:
            on_log(
                "Генерация завершена: "
                f"{optimized.character_count}/{max_characters} символов"
            )

        return TagGenerationResult(
            optimized=optimized,
            base_queries=tuple(base_queries),
            collected_count=collected_count,
            merged_count=len(merged),
            filtered_count=len(filtered),
            generated_count=generated_count,
            expansion=expansion,
        )
