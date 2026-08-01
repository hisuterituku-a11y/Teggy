from __future__ import annotations

from typing import Callable


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

    def __init__(self, llm_client):
        self._llm = llm_client

    def expand(
        self,
        service_name: str,
        address: str = "",
        city: str = "",
        on_log: LogCallback | None = None,
    ) -> list[str]:

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

        result = []

        seen = set()

        for keyword in keywords:

            keyword = " ".join(keyword.split()).strip()

            if not keyword:
                continue

            key = keyword.casefold()

            if key in seen:
                continue

            seen.add(key)

            result.append(keyword)

        if service_name.casefold() not in seen:
            result.insert(0, service_name)

        if on_log:
            on_log(
                f"Получено базовых запросов: {len(result)}"
            )

        return result