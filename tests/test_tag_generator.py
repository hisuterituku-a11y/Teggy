from __future__ import annotations

import pytest

from core.tag_generator import TagGenerator


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Лечение зубов", "lechenie-zubov"),
        ("Ёлка", "yolka"),
        ("Санкт—Петербург", "sankt-peterburg"),
        ("Тест   услуги", "test-uslugi"),
        ("Услуга-24", "usluga-24"),
        ("Мягкий знак ь и твёрдый ъ", "myagkij-znak-i-tvyordyj"),
    ],
)
def test_translit(source: str, expected: str) -> None:
    assert TagGenerator.translit(source) == expected


def test_generate_tags_skips_empty_lines() -> None:
    assert TagGenerator.generate_tags(
        ["Стоматология", "", "   ", "Лечение зубов"]
    ) == [
        "Стоматология;stomatologiya",
        "Лечение зубов;lechenie-zubov",
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Стоматология;stomatologiya", True),
        ("Услуга;service-24", True),
        ("Стоматология;", False),
        (";stomatologiya", False),
        ("Стоматология", False),
        ("Услуга;транслит", False),
        ("Услуга;service name", False),
    ],
)
def test_is_ready_tag(value: str, expected: bool) -> None:
    assert TagGenerator.is_ready_tag(value) is expected


def test_parse_tags_input_preserves_ready_tags() -> None:
    text = "Стоматология;stomatologiya\nЛечение зубов;lechenie-zubov"

    assert TagGenerator.parse_tags_input(text) == [
    "Стоматология;stomatologiya",
    "Лечение зубов;lechenie-zubov",
]


def test_parse_tags_input_generates_tags_when_input_is_mixed() -> None:
    text = "Стоматология;stomatologiya\nЛечение зубов"

    assert TagGenerator.parse_tags_input(text) == [
        "Стоматология;stomatologiya",
        "Лечение зубов;lechenie-zubov",
    ]


def test_generate_seo_tags_preserves_lines_containing_semicolon() -> None:
    assert TagGenerator.generate_seo_tags(
        ["Стоматология;stomatologiya", "Лечение зубов", " "]
    ) == [
        "Стоматология;stomatologiya",
        "Лечение зубов;lechenie-zubov",
    ]
