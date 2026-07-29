# Сборка Teggy для Windows

## Что получается

Скрипт собирает PyInstaller `onedir`, затем упаковывает его в один установщик Inno Setup:

- приложение: `dist\Teggy\Teggy.exe`;
- установщик: `release\TeggySetup-2.1.0-dev.exe`.

## Требования

1. Windows 10/11 x64.
2. Python, доступный через команду `py -3`.
3. Inno Setup 6 для создания установщика.

## Полная сборка

Из корня репозитория:

```powershell
powershell -ExecutionPolicy Bypass -File .\build\build.ps1 -Clean
```

Скрипт сам создаст отдельное окружение `.venv-build`, установит зависимости, соберёт приложение и вызовет Inno Setup.

## Только папка приложения

```powershell
powershell -ExecutionPolicy Bypass -File .\build\build.ps1 -Clean -SkipInstaller
```

## FFmpeg

Если требуется встроить FFmpeg, положите `ffmpeg.exe` в одно из мест до сборки:

```text
tools\ffmpeg.exe
ffmpeg.exe
```

Спецификация автоматически добавит первый найденный файл в папку приложения.

## Перед передачей коллегам

Проверьте установщик на чистом компьютере или в Windows Sandbox:

1. установка без Python;
2. запуск через меню «Пуск»;
3. загрузка тем и ресурсов;
4. скачивание видео;
5. создание диагностического журнала;
6. удаление через «Установленные приложения».
