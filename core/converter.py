"""Конвертация изображений в JPG."""

from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from core.exceptions import ConversionError


class ImageConverter:
    """Конвертирует WebP, PNG, BMP и TIFF в JPG."""

    SUPPORTED_FORMATS = {".webp", ".png", ".bmp", ".tif", ".tiff"}

    @staticmethod
    def convert(
        filepath: Path,
        output_dir: Optional[Path] = None,
        quality: int = 100,
        delete_original: bool = False,
    ) -> Path:
        """Конвертирует одно изображение в JPG.

        При ``delete_original=True`` новый JPG создаётся рядом с исходником,
        после чего исходный файл удаляется. Так режим замены действительно
        заменяет фото, а не переносит результат в чужую папку.
        """
        try:
            filepath = Path(filepath)
            suffix = filepath.suffix.lower()
            if suffix not in ImageConverter.SUPPORTED_FORMATS:
                raise ConversionError(
                    f"Формат {suffix} не поддерживается. "
                    f"Поддерживаемые: {', '.join(sorted(ImageConverter.SUPPORTED_FORMATS))}"
                )

            target_dir = filepath.parent if delete_original else (output_dir or filepath.parent)
            target_dir.mkdir(parents=True, exist_ok=True)
            new_path = target_dir / f"{filepath.stem}.jpg"

            with Image.open(filepath) as image:
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
                elif image.mode == "L":
                    image = image.convert("RGB")
                image.save(new_path, "JPEG", quality=quality, subsampling=0)

            if delete_original and filepath.resolve() != new_path.resolve():
                filepath.unlink()

            return new_path
        except ConversionError:
            raise
        except Exception as error:
            raise ConversionError(f"Ошибка конвертации {filepath.name}: {error}") from error

    @staticmethod
    def convert_batch(
        filepaths: List[Path],
        output_dir: Optional[Path] = None,
        quality: int = 100,
        delete_original: bool = False,
    ) -> Dict[Path, Optional[Path]]:
        results: Dict[Path, Optional[Path]] = {}
        for filepath in filepaths:
            try:
                results[filepath] = ImageConverter.convert(
                    filepath,
                    output_dir,
                    quality,
                    delete_original,
                )
            except ConversionError:
                results[filepath] = None
        return results

    @staticmethod
    def needs_conversion(filepath: Path) -> bool:
        return Path(filepath).suffix.lower() in ImageConverter.SUPPORTED_FORMATS
