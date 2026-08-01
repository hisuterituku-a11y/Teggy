from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable

from .keyword_merger import MergedKeyword


LogCallback = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class OptimizedTags:
    """
    Результат оптимизации тегов.

    text:
        Готовая строка тегов через запятую.

    tags:
        Теги, вошедшие в итоговую строку.

    character_count:
        Количество символов в итоговой строке.

    source_count:
        Количество запросов до оптимизации.
    """

    text: str
    tags: tuple[str, ...]
    character_count: int
    source_count: int


class TagOptimizer:
    """
    Формирует итоговую строку тегов для Яндекс Бизнес.

    Основные задачи:
    - удалить дубли;
    - отсортировать запросы по полезности;
    - учитывать частотность Wordstat;
    - повысить приоритет коммерческих и локальных запросов;
    - уложить результат в заданный лимит символов.
    """

    COMMERCIAL_WORDS = {
        "цена",
        "цены",
        "стоимость",
        "сколько стоит",
        "сколько стоят",
        "заказать",
        "записаться",
        "запись",
        "установить",
        "установка",
        "поставить",
        "под ключ",
        "недорого",
        "купить",
        "консультация",
    }

    TRUST_WORDS = {
        "отзывы",
        "лучшие",
        "лучший",
        "хорошие",
        "до и после",
        "что лучше",
    }

    LOCAL_WORDS = {
        "рядом",
        "рядом со мной",
        "метро",
        "район",
        "улица",
        "проспект",
        "санкт-петербург",
        "спб",
        "москва",
    }

    LOW_PRIORITY_WORDS = {
        "что такое",
        "почему",
        "как выглядит",
        "фото",
        "картинки",
        "видео",
        "википедия",
        "форум",
    }

    def __init__(
        self,
        *,
        max_characters: int = 3000,
        separator: str = ", ",
    ) -> None:
        if max_characters < 1:
            raise ValueError(
                "max_characters должен быть больше нуля"
            )

        if not separator:
            raise ValueError(
                "separator не должен быть пустым"
            )

        self.max_characters = max_characters
        self.separator = separator

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Нормализует пробелы и удаляет лишние разделители.
        Регистр исходной строки сохраняется.
        """

        value = re.sub(
            r"\s+",
            " ",
            str(text),
        )

        return value.strip(" ,;\n\t")

    @staticmethod
    def _contains_any(
        phrase: str,
        words: Iterable[str],
    ) -> bool:
        lowered = phrase.casefold()

        return any(
            word.casefold() in lowered
            for word in words
        )

    def _calculate_score(
        self,
        item: MergedKeyword,
        *,
        service_name: str,
        city: str,
        address: str,
    ) -> float:
        """
        Рассчитывает приоритет запроса.

        Чем выше результат, тем раньше тег попадёт
        в итоговую строку.
        """

        phrase = self._normalize(item.phrase)
        lowered = phrase.casefold()

        score = 0.0

        # Частотность учитывается, но ограниченно.
        # Иначе слишком общий запрос вроде "стоматология"
        # вытеснит все точные коммерческие формулировки.
        score += min(item.frequency, 100_000) / 1000

        service_name = self._normalize(
            service_name
        ).casefold()

        city = self._normalize(city).casefold()
        address = self._normalize(address).casefold()

        # Точное название услуги получает максимальный приоритет.
        if service_name:
            if lowered == service_name:
                score += 1000
            elif service_name in lowered:
                score += 300

        # Коммерческие намерения.
        if self._contains_any(
            lowered,
            self.COMMERCIAL_WORDS,
        ):
            score += 180

        # Запросы доверия и сравнения.
        if self._contains_any(
            lowered,
            self.TRUST_WORDS,
        ):
            score += 100

        # Локальные запросы.
        if self._contains_any(
            lowered,
            self.LOCAL_WORDS,
        ):
            score += 150

        # Конкретный город.
        if city and city in lowered:
            score += 220

        # Части адреса: улица, проспект, метро и так далее.
        if address:
            address_parts = self._extract_address_parts(
                address
            )

            if any(
                part in lowered
                for part in address_parts
            ):
                score += 200

        # Фразы средней длины обычно лучше подходят для тегов.
        word_count = len(phrase.split())

        if 2 <= word_count <= 6:
            score += 40
        elif word_count > 10:
            score -= 80

        # Слишком длинные теги невыгодны при лимите 3000 символов.
        if len(phrase) > 100:
            score -= 100
        elif len(phrase) > 70:
            score -= 40

        # Информационные запросы оставляем, но опускаем ниже.
        if self._contains_any(
            lowered,
            self.LOW_PRIORITY_WORDS,
        ):
            score -= 150

        return score

    def _extract_address_parts(
        self,
        address: str,
    ) -> set[str]:
        """
        Извлекает пригодные для поиска части адреса.

        Например:

        Владимирский проспект, 7

        превращается в:

        {
            "владимирский",
            "проспект",
            "владимирский проспект"
        }
        """

        normalized = self._normalize(
            address
        ).casefold()

        # Убираем номера домов и короткие служебные части.
        words = re.findall(
            r"[а-яёa-z-]+",
            normalized,
            flags=re.IGNORECASE,
        )

        useful_words = {
            word
            for word in words
            if len(word) >= 4
        }

        result = set(useful_words)

        if len(words) >= 2:
            for index in range(len(words) - 1):
                combined = (
                    f"{words[index]} "
                    f"{words[index + 1]}"
                )

                result.add(combined)

        return result

    def _prepare_keywords(
        self,
        keywords: Iterable[MergedKeyword],
    ) -> list[MergedKeyword]:
        """
        Удаляет пустые значения и дубли.

        При совпадении фраз сохраняется вариант
        с максимальной частотностью.
        """

        unique: dict[str, MergedKeyword] = {}

        for item in keywords:
            phrase = self._normalize(item.phrase)

            if not phrase:
                continue

            key = phrase.casefold()
            existing = unique.get(key)

            normalized_item = MergedKeyword(
                phrase=phrase,
                frequency=max(
                    0,
                    int(item.frequency),
                ),
                sources=item.sources,
            )

            if existing is None:
                unique[key] = normalized_item
                continue

            if normalized_item.frequency > existing.frequency:
                unique[key] = normalized_item

        return list(unique.values())

    def optimize(
        self,
        keywords: Iterable[MergedKeyword],
        *,
        service_name: str = "",
        city: str = "",
        address: str = "",
        max_characters: int | None = None,
        on_log: LogCallback | None = None,
    ) -> OptimizedTags:
        """
        Формирует готовую строку тегов.

        Аргументы:
            keywords:
                Запросы после KeywordFilter или AIKeywordFilter.

            service_name:
                Название услуги, например "Элайнеры".

            city:
                Город, например "Санкт-Петербург".

            address:
                Адрес организации.

            max_characters:
                Необязательное переопределение лимита.

            on_log:
                Функция логирования.
        """

        limit = (
            max_characters
            if max_characters is not None
            else self.max_characters
        )

        if limit < 1:
            raise ValueError(
                "Лимит символов должен быть больше нуля"
            )

        prepared = self._prepare_keywords(
            keywords
        )

        source_count = len(prepared)

        ranked = sorted(
            prepared,
            key=lambda item: (
                -self._calculate_score(
                    item,
                    service_name=service_name,
                    city=city,
                    address=address,
                ),
                -item.frequency,
                len(item.phrase),
                item.phrase.casefold(),
            ),
        )

        selected: list[str] = []
        current_length = 0

        for item in ranked:
            phrase = self._normalize(item.phrase)

            if not phrase:
                continue

            added_length = len(phrase)

            if selected:
                added_length += len(self.separator)

            if current_length + added_length > limit:
                continue

            selected.append(phrase)
            current_length += added_length

            if current_length == limit:
                break

        text = self.separator.join(selected)

        result = OptimizedTags(
            text=text,
            tags=tuple(selected),
            character_count=len(text),
            source_count=source_count,
        )

        if on_log:
            on_log(
                "Оптимизация тегов завершена: "
                f"исходных запросов {source_count}, "
                f"выбрано тегов {len(result.tags)}, "
                f"символов {result.character_count}/{limit}"
            )

        return result

    def build_text(
        self,
        keywords: Iterable[MergedKeyword],
        *,
        service_name: str = "",
        city: str = "",
        address: str = "",
        max_characters: int | None = None,
        on_log: LogCallback | None = None,
    ) -> str:
        """
        Упрощённый метод, возвращающий только строку тегов.
        """

        result = self.optimize(
            keywords,
            service_name=service_name,
            city=city,
            address=address,
            max_characters=max_characters,
            on_log=on_log,
        )

        return result.text