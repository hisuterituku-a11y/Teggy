"""
Конвертация изображений в JPG.
"""

from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image

from core.exceptions import ConversionError


class ImageConverter:
    """
    Конвертирует изображения в JPG.

    Поддерживаемые форматы: WebP, PNG, BMP, TIFF.
    """

    SUPPORTED_FORMATS = {'.webp', '.png', '.bmp', '.tif', '.tiff'}

    @staticmethod
    def convert(
        filepath: Path,
        output_dir: Optional[Path] = None,
        quality: int = 100,
        delete_original: bool = False
    ) -> Path:
        """
        Конвертирует одно изображение в JPG.

        Args:
            filepath: путь к файлу
            output_dir: папка для сохранения (если None — рядом с оригиналом)
            quality: качество JPG (1-100)
            delete_original: удалить исходный файл

        Returns:
            путь к новому файлу

        Raises:
            ConversionError: если не удалось конвертировать
        """
        try:
            # Проверяем формат
            suffix = filepath.suffix.lower()
            if suffix not in ImageConverter.SUPPORTED_FORMATS:
                raise ConversionError(
                    f"Формат {suffix} не поддерживается. "
                    f"Поддерживаемые: {', '.join(ImageConverter.SUPPORTED_FORMATS)}"
                )

            # Определяем выходной путь
            if output_dir is None:
                output_dir = filepath.parent

            output_dir.mkdir(parents=True, exist_ok=True)
            new_name = filepath.stem + '.jpg'
            new_path = output_dir / new_name

            # Открываем и конвертируем
            img = Image.open(filepath)

            # Конвертируем в RGB (для JPG)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # Сохраняем как JPG
            img.save(new_path, 'JPEG', quality=quality, subsampling=0)

            # Удаляем оригинал если нужно
            if delete_original:
                filepath.unlink()

            return new_path

        except Exception as e:
            raise ConversionError(f"Ошибка конвертации {filepath.name}: {e}")

    @staticmethod
    def convert_batch(
        filepaths: List[Path],
        output_dir: Optional[Path] = None,
        quality: int = 100,
        delete_original: bool = False
    ) -> Dict[Path, Optional[Path]]:
        """
        Конвертирует несколько изображений в JPG.

        Returns:
            словарь {оригинал: новый_файл или None если ошибка}
        """
        results = {}
        for filepath in filepaths:
            try:
                new_path = ImageConverter.convert(
                    filepath,
                    output_dir,
                    quality,
                    delete_original
                )
                results[filepath] = new_path
            except ConversionError:
                results[filepath] = None
        return results

    @staticmethod
    def needs_conversion(filepath: Path) -> bool:
        """Проверяет, нужно ли конвертировать файл."""
        return filepath.suffix.lower() in ImageConverter.SUPPORTED_FORMATS