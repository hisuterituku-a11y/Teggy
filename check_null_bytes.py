from pathlib import Path

root = Path(r"X:\Teggy")
found = False

print("🔍 Проверяем все .py файлы на наличие NULL-байтов...")
print("=" * 50)

for file in root.rglob("*.py"):
    try:
        data = file.read_bytes()
        if b"\x00" in data:
            print(f"❌ NULL байты найдены в: {file}")
            found = True
    except Exception as e:
        print(f"⚠️ Ошибка при чтении {file}: {e}")

if not found:
    print("✅ NULL байты не найдены ни в одном файле.")
else:
    print("\n❌ Есть файлы с NULL-байтами! Их нужно пересоздать.")