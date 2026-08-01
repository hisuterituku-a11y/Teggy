from core.wordstat.tag_generator import TagGenerator
from core.wordstat.wordstat_collector import WordstatCollector


collector = WordstatCollector(
    headless=False,
)

generator = TagGenerator(
    collector=collector,
)

result = generator.generate(
    service_name="Элайнеры",
    region="2",
    city="Санкт-Петербург",
    address="Владимирский проспект, 7",
    manual_queries=[
        "элайнеры",
        "капы для выравнивания зубов",
        "исправление прикуса элайнерами",
    ],
    max_characters=3000,
    on_log=print,
)

print()
print("=" * 80)
print(result.text)
print("=" * 80)

print(f"Базовых запросов: {len(result.base_queries)}")
print(f"Получено Wordstat: {result.collected_count}")
print(f"После объединения: {result.merged_count}")
print(f"После фильтрации: {result.filtered_count}")
print(f"Итоговых тегов: {len(result.tags)}")
print(f"Символов: {result.character_count}")