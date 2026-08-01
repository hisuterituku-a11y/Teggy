from __future__ import annotations

import json
import re
from collections import Counter
from typing import Callable, Iterable

from .keyword_merger import MergedKeyword


LogCallback = Callable[[str], None]


class KeywordFilter:
    """
    Детерминированная очистка запросов Wordstat.

    Удаляет:
    - дубли;
    - слишком короткие и низкочастотные запросы;
    - маркетплейсы, аптеки и товарные запросы;
    - нежелательные бренды;
    - чужую географию;
    - запросы с годами;
    - явно информационные запросы, если remove_info=True.

    Фильтр не изменяет формулировки и возвращает исходные
    объекты MergedKeyword.
    """

    DEFAULT_BLACKLIST = {
        "википедия", "wiki", "youtube", "ютуб", "авито",
        "ozon", "озон", "wildberries", "вайлдберриз",
        "яндекс маркет", "алиэкспресс", "aliexpress",
    }

    DEFAULT_INFO_WORDS = {
        "что", "почему", "зачем", "как", "какой", "какая",
        "какие", "можно ли", "форум", "фото", "картинки",
        "видео", "скачать", "бесплатно",
    }

    DEFAULT_PRODUCT_TERMS = {
        "в аптеке", "купить в аптеке", "аптека",
        "на маркетплейсе", "для домашнего использования",
        "своими руками", "самостоятельно", "инструкция по применению",
    }

    DEFAULT_BRANDS = {
        "flexiligner", "флексилайнер", "eurokappa", "еврокапа",
        "еврокаппа", "gezatone", "гезатон", "invisalign",
        "инвизилайн", "star smile", "стар смайл",
    }

    DEFAULT_FOREIGN_GEO = {
        "москва", "московская область", "новосибирск", "екатеринбург",
        "казань", "нижний новгород", "челябинск", "самара", "омск",
        "ростов-на-дону", "ростов на дону", "уфа", "красноярск",
        "пермь", "воронеж", "волгоград", "краснодар", "саратов",
        "тюмень", "тольятти", "ижевск", "барнаул", "ульяновск",
        "иркутск", "хабаровск", "ярославль", "владивосток",
        "махачкала", "томск", "оренбург", "кемерово", "новокузнецк",
        "рязань", "астрахань", "набережные челны", "пенза", "липецк",
        "киров", "чебоксары", "тула", "калининград", "балашиха",
        "курск", "севастополь", "сочи", "ставрополь", "тверь",
        "магнитогорск", "иваново", "брянск", "белгород", "сургут",
        "владимир", "архангельск", "череповец", "калуга", "смоленск",
        "вьетнам", "беларусь", "казахстан", "узбекистан", "турция",
        "германия", "израиль",
    }

    CITY_ALIASES = {
        "санкт-петербург": {
            "санкт-петербург", "санкт петербург", "петербург", "спб",
        },
        "москва": {"москва", "мск"},
        "нижний новгород": {"нижний новгород", "нн"},
        "ростов-на-дону": {"ростов-на-дону", "ростов на дону"},
    }

    YEAR_RE = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")

    def __init__(
        self,
        blacklist: set[str] | None = None,
        *,
        product_terms: set[str] | None = None,
        brands: set[str] | None = None,
        foreign_geo: set[str] | None = None,
    ) -> None:
        self.blacklist = self._normalized_set(
            blacklist if blacklist is not None else self.DEFAULT_BLACKLIST
        )
        self.product_terms = self._normalized_set(
            product_terms if product_terms is not None else self.DEFAULT_PRODUCT_TERMS
        )
        self.brands = self._normalized_set(
            brands if brands is not None else self.DEFAULT_BRANDS
        )
        self.foreign_geo = self._normalized_set(
            foreign_geo if foreign_geo is not None else self.DEFAULT_FOREIGN_GEO
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", str(text).strip().lower())

    @classmethod
    def _normalized_set(cls, values: Iterable[str]) -> set[str]:
        return {
            normalized
            for value in values
            if (normalized := cls._normalize(value))
        }

    @staticmethod
    def _contains_term(phrase: str, term: str) -> bool:
        pattern = rf"(?<![\wа-яё]){re.escape(term)}(?![\wа-яё])"
        return re.search(pattern, phrase, flags=re.IGNORECASE) is not None

    @classmethod
    def _contains_any(cls, phrase: str, terms: Iterable[str]) -> bool:
        return any(cls._contains_term(phrase, term) for term in terms)

    @classmethod
    def _city_aliases(
        cls,
        city: str,
        allowed_geo_aliases: Iterable[str] | None,
    ) -> set[str]:
        aliases = cls._normalized_set(allowed_geo_aliases or ())
        normalized_city = cls._normalize(city)

        if not normalized_city:
            return aliases

        aliases.add(normalized_city)

        for canonical, known_aliases in cls.CITY_ALIASES.items():
            normalized_known = cls._normalized_set(known_aliases)
            if normalized_city == canonical or normalized_city in normalized_known:
                aliases.update(normalized_known)
                aliases.add(canonical)

        return aliases

    def _has_foreign_geo(
        self,
        phrase: str,
        *,
        allowed_geo: set[str],
        extra_forbidden_geo: set[str],
    ) -> bool:
        forbidden = self.foreign_geo | extra_forbidden_geo

        for geo in forbidden:
            if geo in allowed_geo:
                continue
            if self._contains_term(phrase, geo):
                return True

        return False

    def filter(
        self,
        keywords: list[MergedKeyword],
        *,
        city: str = "",
        allowed_geo_aliases: Iterable[str] | None = None,
        forbidden_geo: Iterable[str] | None = None,
        remove_info: bool = False,
        remove_years: bool = True,
        remove_brands: bool = True,
        remove_product_queries: bool = True,
        min_length: int = 3,
        min_frequency: int = 1,
        on_log: LogCallback | None = None,
    ) -> list[MergedKeyword]:
        if min_length < 1:
            raise ValueError("min_length должен быть больше нуля")
        if min_frequency < 0:
            raise ValueError("min_frequency не может быть отрицательным")

        allowed_geo = self._city_aliases(city, allowed_geo_aliases)
        extra_forbidden_geo = self._normalized_set(forbidden_geo or ())

        result: list[MergedKeyword] = []
        seen: set[str] = set()
        reasons: Counter[str] = Counter()

        for item in keywords:
            phrase = self._normalize(item.phrase)

            if len(phrase) < min_length:
                reasons["короткие"] += 1
                continue
            if item.frequency < min_frequency:
                reasons["низкая частота"] += 1
                continue

            key = phrase.casefold()
            if key in seen:
                reasons["дубли"] += 1
                continue
            seen.add(key)

            if self._contains_any(phrase, self.blacklist):
                reasons["мусор и маркетплейсы"] += 1
                continue
            if remove_product_queries and self._contains_any(phrase, self.product_terms):
                reasons["товарные запросы"] += 1
                continue
            if remove_brands and self._contains_any(phrase, self.brands):
                reasons["бренды"] += 1
                continue
            if remove_years and self.YEAR_RE.search(phrase):
                reasons["годы"] += 1
                continue
            if self._has_foreign_geo(
                phrase,
                allowed_geo=allowed_geo,
                extra_forbidden_geo=extra_forbidden_geo,
            ):
                reasons["чужая география"] += 1
                continue
            if remove_info and self._contains_any(phrase, self.DEFAULT_INFO_WORDS):
                reasons["информационные"] += 1
                continue

            result.append(item)

        result.sort(key=lambda item: (-item.frequency, item.phrase.casefold()))

        if on_log:
            removed = sum(reasons.values())
            details = ", ".join(
                f"{reason}: {count}" for reason, count in reasons.most_common()
            )
            message = (
                f"Фильтрация завершена. Удалено: {removed}. "
                f"Осталось: {len(result)}."
            )
            if details:
                message += f" Причины: {details}."
            on_log(message)

        return result


AI_FILTER_SYSTEM_PROMPT = """
Ты специалист по поисковым запросам и Яндекс Бизнес.

Твоя задача — отбирать поисковые запросы, подходящие для продвижения
конкретной услуги в карточке организации.

Правила:

1. Оставляй только запросы, которые прямо относятся к указанной услуге.
2. Предпочитай коммерческие, локальные и транзакционные запросы:
   цена, стоимость, заказать, записаться, установить, рядом, отзывы.
3. Допускаются полезные запросы сравнения и выбора:
   что лучше, до и после, отзывы.
4. Удаляй запросы:
   - про другие услуги;
   - про самостоятельное лечение;
   - про обучение и вакансии;
   - про покупку оборудования и материалов;
   - про рефераты, курсовые, картинки, видео и скачивание;
   - с названиями конкурентов и чужих клиник;
   - явно бессмысленные или нерелевантные.
5. Не исправляй и не переформулируй запросы.
6. Не придумывай новые запросы.
7. Возвращай только строки, которые присутствуют во входном списке.
8. Верни только JSON-массив строк без пояснений и Markdown.
""".strip()


class AIKeywordFilter:
    def __init__(self, llm_client, *, chunk_size: int = 150) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size должен быть больше нуля")
        self._llm = llm_client
        self._chunk_size = chunk_size

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", str(text)).strip(" ,;\n\t")

    @staticmethod
    def _split_chunks(
        values: list[MergedKeyword],
        chunk_size: int,
    ) -> Iterable[list[MergedKeyword]]:
        for start in range(0, len(values), chunk_size):
            yield values[start:start + chunk_size]

    def _build_prompt(
        self,
        *,
        service_name: str,
        city: str,
        address: str,
        keywords: list[MergedKeyword],
    ) -> str:
        phrases = [item.phrase for item in keywords]
        return f"""
Услуга:
{service_name}

Город:
{city or "не указан"}

Адрес:
{address or "не указан"}

Ниже приведены реальные поисковые запросы Wordstat.

Отбери только запросы, релевантные указанной услуге и подходящие
для тегов позиции прайс-листа в Яндекс Бизнес.

Сохраняй исходные формулировки без изменений.

Запросы:
{json.dumps(phrases, ensure_ascii=False, indent=2)}

Верни только JSON-массив выбранных строк.
""".strip()

    def _parse_response(self, response: object) -> list[str]:
        parser = getattr(self._llm, "parse_json_array", None)

        if callable(parser):
            parsed = parser(response)
        else:
            if not isinstance(response, str):
                raise TypeError(
                    "Ответ LLM должен быть строкой, если parse_json_array отсутствует"
                )
            text = response.strip()
            if text.startswith("```"):
                text = re.sub(
                    r"^```(?:json)?\s*|\s*```$",
                    "",
                    text,
                    flags=re.IGNORECASE,
                ).strip()
            parsed = json.loads(text)

        if not isinstance(parsed, list):
            raise ValueError("LLM вернула не JSON-массив")

        return [
            self._normalize(value)
            for value in parsed
            if isinstance(value, str) and self._normalize(value)
        ]

    def _filter_chunk(
        self,
        *,
        service_name: str,
        city: str,
        address: str,
        keywords: list[MergedKeyword],
    ) -> list[MergedKeyword]:
        prompt = self._build_prompt(
            service_name=service_name,
            city=city,
            address=address,
            keywords=keywords,
        )
        response = self._llm.chat(system=AI_FILTER_SYSTEM_PROMPT, prompt=prompt)
        selected_phrases = self._parse_response(response)
        original_by_key = {
            self._normalize(item.phrase).casefold(): item for item in keywords
        }

        selected: list[MergedKeyword] = []
        seen: set[str] = set()
        for phrase in selected_phrases:
            key = phrase.casefold()
            if key in seen:
                continue
            original = original_by_key.get(key)
            if original is None:
                continue
            seen.add(key)
            selected.append(original)

        return selected

    def filter(
        self,
        keywords: list[MergedKeyword],
        *,
        service_name: str,
        city: str = "",
        address: str = "",
        keep_on_error: bool = True,
        on_log: LogCallback | None = None,
    ) -> list[MergedKeyword]:
        service_name = self._normalize(service_name)
        city = self._normalize(city)
        address = self._normalize(address)

        if not service_name:
            raise ValueError("Не указано название услуги")
        if not keywords:
            return []

        result: list[MergedKeyword] = []
        chunks = list(self._split_chunks(keywords, self._chunk_size))

        if on_log:
            on_log(
                f"AI-фильтрация: {len(keywords)} запросов, "
                f"{len(chunks)} частей"
            )

        for index, chunk in enumerate(chunks, start=1):
            if on_log:
                on_log(
                    f"AI-фильтрация части {index}/{len(chunks)}: "
                    f"{len(chunk)} запросов"
                )
            try:
                selected = self._filter_chunk(
                    service_name=service_name,
                    city=city,
                    address=address,
                    keywords=chunk,
                )
            except Exception as error:
                if on_log:
                    on_log(f"Ошибка AI-фильтрации части {index}: {error}")
                selected = chunk if keep_on_error else []

            result.extend(selected)

        unique: dict[str, MergedKeyword] = {}
        for item in result:
            key = self._normalize(item.phrase).casefold()
            existing = unique.get(key)
            if existing is None or item.frequency > existing.frequency:
                unique[key] = item

        filtered = list(unique.values())
        filtered.sort(key=lambda item: (-item.frequency, item.phrase.casefold()))

        if on_log:
            on_log(
                f"AI-фильтрация завершена: было {len(keywords)}, "
                f"осталось {len(filtered)}"
            )

        return filtered