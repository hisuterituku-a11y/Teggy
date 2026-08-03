from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, Iterable


LogCallback = Callable[[str], None]


OFFER_ANALYZER_SYSTEM_PROMPT = """
Ты SEO-аналитик для Яндекс Бизнес.

Разбери описание услуги на поисковые сущности. Не генерируй готовую длинную
строку ключевых фраз. Верни только JSON-объект следующего формата:

{
  "services": [],
  "commercial_intents": [],
  "activities": [],
  "formats": [],
  "audiences": [],
  "features": [],
  "time_modifiers": [],
  "geo": {
    "city": [],
    "district": [],
    "metro": [],
    "street": [],
    "landmarks": []
  }
}

Правила:
1. Используй только факты из входного текста.
2. Не добавляй свойства, которых нет в описании.
3. Сохраняй короткие поисковые формулировки.
4. Не включай цены, телефоны и расписание как отдельные сущности.
5. Не возвращай Markdown и пояснения.
""".strip()


@dataclass(frozen=True, slots=True)
class GeoAnalysis:
    city: tuple[str, ...] = ()
    district: tuple[str, ...] = ()
    metro: tuple[str, ...] = ()
    street: tuple[str, ...] = ()
    landmarks: tuple[str, ...] = ()

    @property
    def all_values(self) -> tuple[str, ...]:
        return (
            *self.city,
            *self.district,
            *self.metro,
            *self.street,
            *self.landmarks,
        )


@dataclass(frozen=True, slots=True)
class OfferAnalysis:
    services: tuple[str, ...] = ()
    commercial_intents: tuple[str, ...] = ()
    activities: tuple[str, ...] = ()
    formats: tuple[str, ...] = ()
    audiences: tuple[str, ...] = ()
    features: tuple[str, ...] = ()
    time_modifiers: tuple[str, ...] = ()
    geo: GeoAnalysis = GeoAnalysis()


class OfferAnalyzer:
    def __init__(self, llm_client) -> None:
        self._llm = llm_client

    @staticmethod
    def _normalize(value: object) -> str:
        return re.sub(r"\s+", " ", str(value)).strip(" ,;\n\t")

    @classmethod
    def _normalize_values(cls, values: object) -> tuple[str, ...]:
        if not isinstance(values, Iterable) or isinstance(values, (str, bytes, dict)):
            return ()

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

        return tuple(result)

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        value = text.strip()
        if value.startswith("```"):
            value = re.sub(
                r"^```(?:json)?\s*|\s*```$",
                "",
                value,
                flags=re.IGNORECASE,
            ).strip()
        return value

    def _parse_object(self, response: object) -> dict:
        parser = getattr(self._llm, "parse_json_object", None)
        if callable(parser):
            parsed = parser(response)
        else:
            if not isinstance(response, str):
                raise TypeError("Ответ LLM должен быть строкой")
            parsed = json.loads(self._strip_code_fence(response))

        if not isinstance(parsed, dict):
            raise ValueError("LLM вернула не JSON-объект")

        return parsed

    def analyze(
        self,
        *,
        offer_text: str,
        service_name: str = "",
        city: str = "",
        address: str = "",
        on_log: LogCallback | None = None,
    ) -> OfferAnalysis:
        offer_text = self._normalize(offer_text)
        service_name = self._normalize(service_name)
        city = self._normalize(city)
        address = self._normalize(address)

        if not offer_text and not service_name:
            raise ValueError("Не указано описание предложения")

        if on_log:
            on_log("Анализируем услугу, условия и географию")

        prompt = f"""
Название услуги:
{service_name or "не указано"}

Город:
{city or "не указан"}

Адрес:
{address or "не указан"}

Описание предложения:
{offer_text or service_name}

Верни только JSON-объект по заданной схеме.
""".strip()

        response = self._llm.chat(
            system=OFFER_ANALYZER_SYSTEM_PROMPT,
            prompt=prompt,
        )
        payload = self._parse_object(response)
        geo_payload = payload.get("geo")
        if not isinstance(geo_payload, dict):
            geo_payload = {}

        services = list(self._normalize_values(payload.get("services")))
        if service_name and service_name.casefold() not in {
            item.casefold() for item in services
        }:
            services.insert(0, service_name)

        geo_city = list(self._normalize_values(geo_payload.get("city")))
        if city and city.casefold() not in {item.casefold() for item in geo_city}:
            geo_city.insert(0, city)

        analysis = OfferAnalysis(
            services=tuple(services),
            commercial_intents=self._normalize_values(
                payload.get("commercial_intents")
            ),
            activities=self._normalize_values(payload.get("activities")),
            formats=self._normalize_values(payload.get("formats")),
            audiences=self._normalize_values(payload.get("audiences")),
            features=self._normalize_values(payload.get("features")),
            time_modifiers=self._normalize_values(payload.get("time_modifiers")),
            geo=GeoAnalysis(
                city=tuple(geo_city),
                district=self._normalize_values(geo_payload.get("district")),
                metro=self._normalize_values(geo_payload.get("metro")),
                street=self._normalize_values(geo_payload.get("street")),
                landmarks=self._normalize_values(geo_payload.get("landmarks")),
            ),
        )

        if on_log:
            on_log(
                "Анализ предложения завершён: "
                f"услуг {len(analysis.services)}, "
                f"гео-точек {len(analysis.geo.all_values)}"
            )

        return analysis
