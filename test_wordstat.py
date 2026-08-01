from core.wordstat.wordstat_collector import WordstatCollector


def print_log(message: str) -> None:
    print(message)


collector = WordstatCollector(
    headless=False,
)

results = collector.collect(
    query="ремонт телефонов",
    region="all",
    on_log=print_log,
)

print()
print(f"Всего запросов: {len(results)}")

for item in results[:30]:
    print(
        f"{item.frequency:>10} | {item.phrase}"
    )