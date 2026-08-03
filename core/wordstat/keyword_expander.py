from __future__ import annotations

from typing import Callable

from .keyword_matrix_builder import KeywordExpansion, KeywordMatrixBuilder
from .offer_analyzer import OfferAnalyzer


LogCallback = Callable[[str], None]


SYSTEM_PROMPT = """
Ты SEO-специалист по Яндекс Бизнес.

Твоя задача — НЕ генерировать сотни ключей.

Нужно определить основные поисковые направления,
по которым люди ищут данную услугу.

Верни только JSON-массив строк.

Не более 15 элементов.

Пример:

[
  "элайнеры",
  "капы для выравнивания зубов",
  "исправление прикуса",
  "выравнивание зубов",
  "ортодонт"
]

Без пояснений.
"""


class KeywordExpander:
    def __init__(
        self,
        llm_client,
        *,
        matrix_builder: KeywordMatrixBuilder | None = None,
    ) -> None:
        self._llm = llm_client
        self._offer_analyzer = OfferAnalyzer(llm_client)
        self._matrix_builder = matrix_builder or KeywordMatrixBuilder()

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(str(value).split()).strip(" ,;\n\t")

    def expand(
        self,
        service_name: str,
        address: str = "",
        city: str = "",
        on_log: LogCallback | None = None,
    ) -> list[str]:
        """Возвращает короткий список базовых запросов для Wordstat."""

        if on_log:
            on_log(
                f"Подбираем базовые запросы для '{service_name}'"
            )

        prompt = f"""
Услуга:
{service_name}

Город:
{city}

Адрес:
{address}

Определи все основные поисковые направления.

Верни только JSON-массив.
"""

        response = self._llm.chat(
            system=SYSTEM_PROMPT,
            prompt=prompt,
        )

        keywords = self._llm.parse_json_array(response)
        result: list[str] = []
        seen: set[str] = set()

        for keyword in keywords:
            normalized = self._normalize(keyword)
            if not normalized:
                continue

            key = normalized.casefold()
            if key in seen:
                continue

            seen.add(key)
            result.append(normalized)

        normalized_service = self._normalize(service_name)
        if (
            normalized_service
            and normalized_service.casefold() not in seen
        ):
            result.insert(0, normalized_service)

        if on_log:
            on_log(
                f"Получено базовых запросов: {len(result)}"
            )

        return result

    def expand_offer(
        self,
        *,
        offer_text: str,
        service_name: str = "",
        address: str = "",
        city: str = "",
        on_log: LogCallback | None = None,
    ) -> KeywordExpansion:
        """
        Разбирает полное описание предложения и строит:
        - короткий список базовых запросов для Wordstat;
        - контролируемую матрицу локальных и коммерческих фраз.
        """

        analysis = self._offer_analyzer.analyze(
            offer_text=offer_text,
            service_name=service_name,
            city=city,
            address=address,
            on_log=on_log,
        )

        return self._matrix_builder.build(
            analysis,
            on_log=on_log,
        )
