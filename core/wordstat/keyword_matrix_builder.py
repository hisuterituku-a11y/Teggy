from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable

from .offer_analyzer import OfferAnalysis


LogCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class GeneratedKeyword:
    phrase: str
    cluster: str
    priority: int
    generated_from: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KeywordExpansion:
    analysis: OfferAnalysis
    seed_queries: tuple[str, ...]
    generated_keywords: tuple[GeneratedKeyword, ...]


class KeywordMatrixBuilder:
    """Строит контролируемые поисковые фразы из анализа предложения."""

    def __init__(
        self,
        *,
        max_seed_queries: int = 24,
        max_generated_keywords: int = 220,
    ) -> None:
        if max_seed_queries < 1:
            raise ValueError("max_seed_queries должен быть больше нуля")
        if max_generated_keywords < 1:
            raise ValueError("max_generated_keywords должен быть больше нуля")

        self.max_seed_queries = max_seed_queries
        self.max_generated_keywords = max_generated_keywords

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", str(value)).strip(" ,;\n\t")

    @classmethod
    def _unique(cls, values: Iterable[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for raw_value in values:
            value = cls._normalize(raw_value)
            if not value:
                continue
            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(value)

        return result

    def _add(
        self,
        target: list[GeneratedKeyword],
        seen: set[str],
        phrase: str,
        *,
        cluster: str,
        priority: int,
        generated_from: Iterable[str],
    ) -> None:
        if len(target) >= self.max_generated_keywords:
            return

        normalized = self._normalize(phrase)
        if not normalized:
            return

        key = normalized.casefold()
        if key in seen:
            return

        seen.add(key)
        target.append(
            GeneratedKeyword(
                phrase=normalized,
                cluster=cluster,
                priority=priority,
                generated_from=tuple(self._unique(generated_from)),
            )
        )

    def build(
        self,
        analysis: OfferAnalysis,
        *,
        on_log: LogCallback | None = None,
    ) -> KeywordExpansion:
        services = self._unique(analysis.services)
        intents = self._unique(analysis.commercial_intents)
        activities = self._unique(analysis.activities)
        formats = self._unique(analysis.formats)
        audiences = self._unique(analysis.audiences)
        features = self._unique(analysis.features)
        time_modifiers = self._unique(analysis.time_modifiers)

        cities = self._unique(analysis.geo.city)
        districts = self._unique(analysis.geo.district)
        metros = self._unique(analysis.geo.metro)
        streets = self._unique(analysis.geo.street)
        landmarks = self._unique(analysis.geo.landmarks)
        general_geo = self._unique((*cities, *districts))

        generated: list[GeneratedKeyword] = []
        seen: set[str] = set()

        for service in services:
            self._add(
                generated,
                seen,
                service,
                cluster="service",
                priority=1000,
                generated_from=(service,),
            )

            for intent in intents:
                self._add(
                    generated,
                    seen,
                    f"{intent} {service}",
                    cluster="commercial",
                    priority=900,
                    generated_from=(intent, service),
                )

            for geo in general_geo:
                self._add(
                    generated,
                    seen,
                    f"{service} {geo}",
                    cluster="geo",
                    priority=860,
                    generated_from=(service, geo),
                )

            for metro in metros:
                self._add(
                    generated,
                    seen,
                    f"{service} у метро {metro}",
                    cluster="metro",
                    priority=880,
                    generated_from=(service, metro),
                )
                self._add(
                    generated,
                    seen,
                    f"{service} рядом с метро {metro}",
                    cluster="metro",
                    priority=870,
                    generated_from=(service, metro),
                )

            for street in streets:
                self._add(
                    generated,
                    seen,
                    f"{service} на {street}",
                    cluster="street",
                    priority=820,
                    generated_from=(service, street),
                )

            for landmark in landmarks:
                self._add(
                    generated,
                    seen,
                    f"{service} рядом с {landmark}",
                    cluster="landmark",
                    priority=800,
                    generated_from=(service, landmark),
                )

            for feature in features:
                self._add(
                    generated,
                    seen,
                    f"{feature} {service}",
                    cluster="feature",
                    priority=740,
                    generated_from=(feature, service),
                )

            for audience in audiences:
                self._add(
                    generated,
                    seen,
                    f"{service} для {audience}",
                    cluster="audience",
                    priority=650,
                    generated_from=(service, audience),
                )

            for time_modifier in time_modifiers:
                self._add(
                    generated,
                    seen,
                    f"{service} {time_modifier}",
                    cluster="time",
                    priority=620,
                    generated_from=(service, time_modifier),
                )

        for activity in activities:
            for service in services:
                self._add(
                    generated,
                    seen,
                    f"{activity} {service}",
                    cluster="activity",
                    priority=780,
                    generated_from=(activity, service),
                )

                for geo in general_geo[:4]:
                    self._add(
                        generated,
                        seen,
                        f"{activity} {service} {geo}",
                        cluster="activity_geo",
                        priority=760,
                        generated_from=(activity, service, geo),
                    )

        for format_value in formats:
            for service in services:
                self._add(
                    generated,
                    seen,
                    f"{format_value} {service}",
                    cluster="format",
                    priority=700,
                    generated_from=(format_value, service),
                )

        generated.sort(
            key=lambda item: (
                -item.priority,
                len(item.phrase),
                item.phrase.casefold(),
            )
        )

        seed_candidates: list[str] = []
        seed_candidates.extend(services)
        seed_candidates.extend(
            item.phrase
            for item in generated
            if item.cluster in {
                "commercial",
                "activity",
                "geo",
                "metro",
                "feature",
                "format",
            }
        )
        seed_queries = tuple(
            self._unique(seed_candidates)[: self.max_seed_queries]
        )

        if on_log:
            on_log(
                "Матрица запросов построена: "
                f"базовых запросов {len(seed_queries)}, "
                f"сгенерированных фраз {len(generated)}"
            )

        return KeywordExpansion(
            analysis=analysis,
            seed_queries=seed_queries,
            generated_keywords=tuple(generated),
        )
