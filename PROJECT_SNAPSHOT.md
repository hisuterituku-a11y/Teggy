# 📋 Teggy 2.1.0 — Полная сводка для разработчика

## Что такое Teggy

Десктопное приложение на PySide6 для пакетной записи EXIF-метаданных и SEO-тегов в фотографии. Основные пользователи — фотографы, клиники, SEO-специалисты.

---

## 1. Где лежит проект

```
X:\Teggy\
├── main.py                 # Точка входа
├── core/                   # Бизнес-логика (без Qt)
│   ├── paths.py            # resource_path() — работает в .exe и dev
│   ├── settings.py         # JSON-настройки (~/.teggy/settings.json)
│   ├── metadata/           # Чтение/запись EXIF (XP-поля, без ImageDescription)
│   ├── converter.py        # PNG/WebP/BMP/TIFF → JPG
│   ├── tag_generator.py    # SEO-теги "русский;translit"
│   ├── template_manager.py # CRUD шаблонов в templates/
│   ├── photo_import/       # НОВЫЙ МОДУЛЬ: импорт из Яндекс Карт
│   │   ├── service.py      # Фасад для GUI
│   │   ├── worker.py       # QThread-воркер
│   │   ├── downloader.py   # Многопоточное скачивание
│   │   ├── providers.py    # YandexParser (Playwright)
│   │   └── models.py       # Dataclass + исключения
│   └── svg_loader.py       # Перекраска SVG через currentColor
├── gui/                    # Интерфейс PySide6
│   ├── main_window.py      # Главное окно
│   ├── sidebar.py          # Навигация (+ Импорт)
│   ├── pages/
│   │   ├── metadata_page.py    # Основная страница
│   │   ├── templates_page.py   # Шаблоны
│   │   └── yandex_downloader_page.py  # НОВАЯ СТРАНИЦА
│   └── theme/              # Система тем (JSON + QSS с @переменными)
├── assets/
│   ├── icons/              # SVG с currentColor
│   └── themes/             # 5 тем: dark, light, sakura, frog, corporate, default
│       └── */background.svg # Фоны для каждой темы
└── templates/              # Пользовательские JSON-шаблоны
```

---

## 2. Ключевые решения (почему так, а не иначе)

| Решение | Причина |
|---------|---------|
| `core` не знает про PySide6 | Чистое разделение слоёв, можно тестировать без GUI |
| `threading.Thread` → `QThread` | Для безопасного обновления UI из фона |
| Сигналы с `QueuedConnection` | Чтобы UI обновлялся в главном потоке |
| `resource_path()` | Единый менеджер путей для dev и .exe |
| `currentColor` в SVG | Иконки перекрашиваются через `svg_loader.py` |
| `QFrame[class="Card"]` вместо `.Card` | В Qt так работают динамические свойства |
| `WA_StyledBackground` | Без этого QFrame не принимает QSS |

---

## 3. Новая фича: Яндекс Карты

### Как работает

1. Пользователь вставляет ссылку на организацию
2. `YandexParser` (Playwright) открывает страницу, собирает URL фотографий
3. `Downloader` скачивает файлы многопоточно
4. Прогресс и логи идут в GUI через сигналы

### Важные файлы

```
core/photo_import/
├── service.py       # PhotoImportService — фасад
├── worker.py        # ImportWorker (QThread)
├── downloader.py    # Downloader (ThreadPoolExecutor)
├── providers.py     # YandexParser (Playwright, headless=False)
└── models.py        # PhotoInfo, ImportTask, ImportProgress, ImportStatus

gui/pages/yandex_downloader_page.py  # Страница в интерфейсе
```

### Особенности

- **Playwright**: браузер видимый (`headless=False`), потому что headless не перехватывает ответы
- **Статусы**: `ImportStatus.SUCCESS`, `FAILED`, `SKIP`, `CANCELLED`
- **Прогресс**: через сигнал `progress_updated` с `QueuedConnection`
- **Отмена**: `stop_import()` → `QThread.quit()`

---

## 4. Система иконок

### Как работает

1. SVG-файлы содержат `fill="currentColor"` и `stroke="currentColor"`
2. `svg_loader.py` заменяет `currentColor` на цвет из темы
3. `IconButton` хранит цвет и перезагружается при смене темы
4. `ThemeManager.apply_theme_to_buttons()` проходит по дереву виджетов

### Ключевые файлы

```
core/svg_loader.py          # Загрузка и перекраска
gui/widgets/buttons.py      # IconButton (reload_icon, set_color)
gui/theme/manager.py        # apply_theme_to_buttons()
assets/themes/*/theme.json  # "icon": "#FFFFFF"
```

---

## 5. Частые ошибки и решения

| Проблема | Решение |
|----------|---------|
| **Иконки белые** | В `theme.json` нет `"icon"`, или SVG без `currentColor` |
| **`QBackingStore::endPaint()`** | UI обновляется из рабочего потока → использовать `QueuedConnection` |
| **`QThread: Destroyed while running`** | Не вызывать `wait()` внутри `finished` → использовать `deleteLater` |
| **Ошибка импорта** | Проверить `__init__.py` в папках |
| **Парсер не находит фото** | В headless-режиме Яндекс отдаёт другой DOM → оставить `headless=False` |
| **Кнопки серые** | Селектор `QPushButton[class="..."]` не работает → использовать `variant` |
| **Карточки без скругления** | Добавить `WA_StyledBackground` в `Card`, `CardHeader`, `CardBody` |

---

## 6. Как собрать EXE

```powershell
cd X:\Teggy
pyinstaller --onefile --windowed --name="Teggy" --add-data "assets;assets" --add-data "templates;templates" main.py
```

Или через `.spec`:

```powershell
pyinstaller Teggy.spec
```

Готовый файл: `dist/Teggy.exe`

---

## 7. Как обновить релиз на GitHub

```powershell
git add .
git commit -m "Release v2.1.0: Yandex photo importer"
git push origin master
```

Затем на GitHub: **Releases → New release** → Tag `v2.1.0`, прикрепить `Teggy.exe` или архив.

---

## 8. Важные пути в коде

- `resource_path("assets/themes")` — темы
- `resource_path("assets/icons")` — иконки
- `Path.home() / ".teggy" / "settings.json"` — настройки
- `Path("templates")` — шаблоны (относительно корня)

---

## 9. Команды для отладки

```powershell
# Очистка кэша
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force

# Проверка JSON-файлов тем
Get-ChildItem -Path assets\themes -Recurse -Filter theme.json | ForEach-Object {
    try { $null = Get-Content $_.FullName -Raw | ConvertFrom-Json; Write-Host "✅ $($_.FullName)" } catch { Write-Host "❌ $($_.FullName)" }
}

# Проверка SVG на currentColor
Get-ChildItem -Path assets\icons -Recurse -Filter *.svg | ForEach-Object {
    if ((Get-Content $_.FullName -Raw) -notmatch 'currentColor') {
        Write-Host "❌ $($_.Name)" -ForegroundColor Red
    }
}
```

---

## 10. Что можно добавить в будущем

1. **Google Maps**, **2GIS** — новые парсеры в `providers.py`
2. **Автообновление** — через GitHub Releases
3. **Горячие клавиши** — Ctrl+O, Ctrl+S, Ctrl+A
4. **Контекстное меню Windows** — ПКМ → Teggy

---

Сохрани этот файл как `PROJECT_SNAPSHOT.md` в корне проекта. 🚀