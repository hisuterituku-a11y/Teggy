"""
Тесты для TagGenerator.
"""

import unittest
from core.tag_generator import TagGenerator


class TestTagGenerator(unittest.TestCase):
    """Тесты TagGenerator."""

    def test_translit(self):
        """Проверка транслитерации."""
        test_cases = [
            ("Лечение зубов", "lechenie-zubov"),
            ("Стоматология", "stomatologiya"),
            ("Имплантация", "implantaciya"),
            ("Хирург", "hirurg"),  # х → h
            ("3D диагностика", "3d-diagnostika"),
            ("Air Flow", "air-flow"),
        ]
        for rus, expected in test_cases:
            with self.subTest(rus=rus):
                self.assertEqual(TagGenerator.translit(rus), expected)

    def test_generate_tags(self):
        """Проверка генерации тегов."""
        services = ["Стоматология", "Лечение зубов"]
        expected = ["Стоматология;stomatologiya", "Лечение зубов;lechenie-zubov"]
        self.assertEqual(TagGenerator.generate_tags(services), expected)

    def test_parse_tags_input_ready(self):
        """Проверка парсинга готовых тегов."""
        text = "Стоматология;stomatologiya\nЛечение;lechenie"
        expected = ["Стоматология;stomatologiya", "Лечение;lechenie"]
        self.assertEqual(TagGenerator.parse_tags_input(text), expected)

    def test_parse_tags_input_generate(self):
        """Проверка парсинга услуг (генерация тегов)."""
        text = "Стоматология\nЛечение зубов"
        expected = ["Стоматология;stomatologiya", "Лечение зубов;lechenie-zubov"]
        self.assertEqual(TagGenerator.parse_tags_input(text), expected)

    def test_is_ready_tag(self):
        """Проверка определения готового тега."""
        self.assertTrue(TagGenerator.is_ready_tag("Стоматология;stomatologiya"))
        self.assertFalse(TagGenerator.is_ready_tag("Стоматология;"))
        self.assertFalse(TagGenerator.is_ready_tag("Стоматология"))


if __name__ == "__main__":
    unittest.main()