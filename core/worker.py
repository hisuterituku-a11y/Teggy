"""
Оркестратор обработки фотографий.

Связывает все модули core в единый процесс:
1. Поиск файлов
2. Конвертация (если нужно)
3. Генерация тегов
4. Запись метаданных
5. Логирование
"""

from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime
import time

from core.exceptions import TegiError, MetadataError, ConversionError
from core.metadata import MetadataWriter
from core.converter import ImageConverter
from core.tag_generator import TagGenerator


class ProcessingWorker:
    """
    Оркестратор обработки фотографий.
    
    Использование:
        worker = ProcessingWorker()
        worker.set_metadata(
            title="Клиника",
            subject="Лечение",
            comment="+7 (999) 123-45-67",
            artist="Клиника",
            copyright="ООО Клиника",
            rating=5
        )
        worker.set_tags(["Стоматология", "Лечение зубов"])
        results = worker.process_folder("X:/Photos")
    """

    def __init__(self):
        """Инициализирует оркестратор."""
        self.metadata_writer = MetadataWriter()
        self.tags: List[str] = []
        self.delete_original: bool = False
        self.quality: int = 100
        self._on_progress: Optional[Callable] = None
        self._on_log: Optional[Callable] = None

    def set_metadata(self, **kwargs) -> None:
        """
        Устанавливает метаданные для записи.
        
        Args:
            title: название
            subject: тема
            comment: комментарий
            artist: автор
            copyright: авторские права
            rating: рейтинг (1-5)
        """
        self.metadata_writer.set_metadata(**kwargs)

    def set_tags(self, tags: List[str]) -> None:
        """
        Устанавливает теги.
        
        Args:
            tags: список тегов (русский;translit или только русские)
        """
        self.tags = tags

    def set_processing_options(
        self,
        delete_original: bool = False,
        quality: int = 100
    ) -> None:
        """
        Устанавливает опции обработки.
        
        Args:
            delete_original: удалять исходные файлы после конвертации
            quality: качество JPG (1-100)
        """
        self.delete_original = delete_original
        self.quality = quality

    def set_callbacks(
        self,
        on_progress: Optional[Callable] = None,
        on_log: Optional[Callable] = None
    ) -> None:
        """
        Устанавливает callback-функции для обратной связи.
        
        Args:
            on_progress: вызывается при обновлении прогресса (current, total)
            on_log: вызывается при логировании (message)
        """
        self._on_progress = on_progress
        self._on_log = on_log

    def _log(self, message: str) -> None:
        """Отправляет сообщение в лог."""
        if self._on_log:
            self._on_log(message)

    def _progress(self, current: int, total: int) -> None:
        """Отправляет обновление прогресса."""
        if self._on_progress:
            self._on_progress(current, total)

    def process_folder(
        self,
        folder_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Обрабатывает все фотографии в папке.
        
        Args:
            folder_path: путь к папке с фото
            output_dir: папка для сохранения результатов
            
        Returns:
            словарь со статистикой:
            {
                "total": int,
                "processed": int,
                "converted": int,
                "failed": int,
                "errors": List[str]
            }
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise TegiError(f"Папка не найдена: {folder_path}")

        # Собираем все изображения
        images = []
        for ext in ['.jpg', '.jpeg', '.webp', '.png', '.bmp', '.tif', '.tiff']:
            images.extend(folder.glob(f"*{ext}"))
            images.extend(folder.glob(f"*{ext.upper()}"))

        # Убираем дубликаты
        images = list(set(images))

        if not images:
            self._log("❌ Нет поддерживаемых файлов")
            return {
                "total": 0,
                "processed": 0,
                "converted": 0,
                "failed": 0,
                "errors": []
            }

        self._log(f"📸 Найдено файлов: {len(images)}")

        # Определяем папку для результатов
        if output_dir is None:
            output_dir = str(folder / "Tegi")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Подготавливаем теги
        tags = self.tags
        if not tags:
            self._log("⚠️ Теги не заданы, обработка пропущена")
            return {
                "total": len(images),
                "processed": 0,
                "converted": 0,
                "failed": 0,
                "errors": ["Теги не заданы"]
            }

        self._log(f"🏷️ Тегов: {len(tags)}")

        # Обрабатываем файлы
        stats = {
            "total": len(images),
            "processed": 0,
            "converted": 0,
            "failed": 0,
            "errors": []
        }

        for idx, img_path in enumerate(images, 1):
            self._log(f"\n→ [{idx}/{stats['total']}] {img_path.name}")

            try:
                # Проверяем, нужно ли конвертировать
                current_file = img_path
                if ImageConverter.needs_conversion(img_path):
                    self._log(f"   🔄 Конвертация: {img_path.name}")
                    try:
                        current_file = ImageConverter.convert(
                            img_path,
                            output_path,
                            quality=self.quality,
                            delete_original=self.delete_original
                        )
                        stats["converted"] += 1
                        self._log(f"   ✅ Сохранён: {current_file.name}")
                    except ConversionError as e:
                        self._log(f"   ❌ Ошибка конвертации: {e}")
                        stats["failed"] += 1
                        stats["errors"].append(str(e))
                        continue

                # Выбираем тег для текущего файла
                tag = tags[(idx - 1) % len(tags)]

                # Записываем метаданные
                self._log(f"   🏷️ Тег: {tag}")
                try:
                    self.metadata_writer.set_metadata(keywords=tag)
                    self.metadata_writer.write(current_file)
                    stats["processed"] += 1
                    self._log(f"   ✅ Метаданные записаны")
                except MetadataError as e:
                    self._log(f"   ❌ Ошибка записи: {e}")
                    stats["failed"] += 1
                    stats["errors"].append(str(e))

            except Exception as e:
                self._log(f"   ❌ Критическая ошибка: {e}")
                stats["failed"] += 1
                stats["errors"].append(str(e))

            self._progress(idx, stats["total"])

        # Итоги
        self._log("\n" + "=" * 55)
        self._log("✅ ОБРАБОТКА ЗАВЕРШЕНА")
        self._log("=" * 55)
        self._log(f"📸 Всего: {stats['total']}")
        self._log(f"🔄 Сконвертировано: {stats['converted']}")
        self._log(f"🏷️ Протегировано: {stats['processed']}")
        self._log(f"❌ Ошибок: {stats['failed']}")

        return stats

    def process_single(
        self,
        file_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Обрабатывает одно изображение.
        
        Args:
            file_path: путь к файлу
            output_dir: папка для сохранения
            
        Returns:
            словарь со статусом
        """
        filepath = Path(file_path)
        if not filepath.exists():
            raise TegiError(f"Файл не найден: {file_path}")

        # Определяем папку для результатов
        if output_dir is None:
            output_dir = str(filepath.parent / "Tegi")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Подготавливаем теги
        tags = self.tags
        if not tags:
            raise TegiError("Теги не заданы")

        try:
            current_file = filepath
            if ImageConverter.needs_conversion(filepath):
                current_file = ImageConverter.convert(
                    filepath,
                    output_path,
                    quality=self.quality,
                    delete_original=self.delete_original
                )

            tag = tags[0]  # Для одного файла берём первый тег
            self.metadata_writer.set_metadata(keywords=tag)
            self.metadata_writer.write(current_file)

            return {
                "success": True,
                "file": str(current_file),
                "converted": current_file != filepath,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "file": str(filepath),
                "converted": False,
                "error": str(e)
            }