"""
Генерация SEO-тегов из списка услуг.

Умное определение:
- Если строка содержит ';' и похожа на готовый тег → используется как есть
- Если только русские названия → генерируется транслит
"""

import re
from typing import List


class TagGenerator:
    """
    Генерирует SEO-теги в формате "русский;translit".
    """

    # Словарь транслитерации (SEO-формат)
    TRANSLIT_MAP = {
    'а': 'a',
    'б': 'b',
    'в': 'v',
    'г': 'g',
    'д': 'd',
    'е': 'e',
    'ё': 'yo',
    'ж': 'zh',
    'з': 'z',
    'и': 'i',
    'й': 'j',
    'к': 'k',
    'л': 'l',
    'м': 'm',
    'н': 'n',
    'о': 'o',
    'п': 'p',
    'р': 'r',
    'с': 's',
    'т': 't',
    'у': 'u',
    'ф': 'f',
    'х': 'h',
    'ц': 'c',
    'ч': 'ch',
    'ш': 'sh',
    'щ': 'shch',
    'ы': 'y',
    'э': 'e',
    'ю': 'yu',
    'я': 'ya'
}

    @staticmethod
    def translit(text: str) -> str:
        """
        Преобразует русский текст в SEO-транслит.

        Правила:
        - все буквы строчные
        - пробелы → дефис
        - дефисы → дефис
        - ь и ъ удаляются
        - английские буквы и цифры сохраняются
        """
        text = text.lower()
        result = ""

        for char in text:
            if char in TagGenerator.TRANSLIT_MAP:
                result += TagGenerator.TRANSLIT_MAP[char]
            elif char in ("ь", "ъ"):
                continue
            elif char in (" ", "-", "—", "–"):
                result += "-"
            else:
                result += char

        result = re.sub(r"-+", "-", result)
        result = result.strip("-")

        return result

    @staticmethod
    def parse_tags_input(text: str) -> List[str]:
        """
        Разбирает введённый текст на теги.

        Если строка уже является готовым тегом — оставляет её как есть.
        Иначе генерирует транслит.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        result = []

        for line in lines:
            if TagGenerator.is_ready_tag(line):
                result.append(line)
            else:
                result.extend(TagGenerator.generate_tags([line]))

        return result
    @staticmethod
    def generate_tags(services: List[str]) -> List[str]:
        """
        Генерирует теги в формате "русский;translit".
        Пустые строки пропускаются.
        """
        result = []

        for service in services:
            service = service.strip()

            if not service:
                continue

            result.append(f"{service};{TagGenerator.translit(service)}")

        return result
    
    @staticmethod
    def is_ready_tag(tag: str) -> bool:
        """
        Определяет, является ли строка готовым тегом.

        Готовый тег должен содержать ';' и осмысленный текст после него.

        Примеры:
            "Стоматология;stomatologiya" → True
            "Стоматология;" → False
            "Стоматология" → False
        """
        if ';' not in tag:
            return False

        parts = tag.split(';', 1)
        if len(parts) != 2:
            return False

        rus, eng = parts
        if not rus.strip() or not eng.strip():
            return False

        # Проверяем, что в английской части только латиница, цифры и дефисы
        eng_clean = eng.strip()
        return bool(re.match(r'^[a-zA-Z0-9\-]+$', eng_clean))

    @staticmethod
    def parse_tags_input(text: str) -> List[str]:
        """
        Разбирает введённый текст на теги.

        Готовые теги сохраняются без изменений.
        Для обычных строк генерируется транслит.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        result = []

        for line in lines:
            if TagGenerator.is_ready_tag(line):
                result.append(line)
            else:
                result.extend(TagGenerator.generate_tags([line]))

        return result
    @staticmethod
    def generate_seo_tags(lines: List[str]) -> List[str]:
        """
        Преобразует список строк в SEO-теги.
        
        Если строка уже содержит ';', она не изменяется.
        Иначе добавляется транслит через ';'.
        
        Args:
            lines: Список строк (услуги или уже готовые теги)
            
        Returns:
            List[str]: Список тегов в формате "оригинал;транслит"
        """
        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if ';' in line:
                result.append(line)
            else:
                translit = TagGenerator.translit(line)
                result.append(f"{line};{translit}")
        
        return result