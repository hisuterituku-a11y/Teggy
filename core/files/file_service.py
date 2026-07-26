from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class FileInfo:
    """Информация о файле."""
    name: str
    path: Path
    size: int
    modified: datetime

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    @property
    def size_kb(self) -> float:
        return self.size / 1024

    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)

    def size_str(self) -> str:
        """Возвращает размер в удобном формате."""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        return f"{self.size / (1024 * 1024 * 1024):.2f} GB"


class FileService:
    """Сервис для работы с файлами."""
    
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}

    @staticmethod
    def is_image(file_path: Path) -> bool:
        """Проверяет, является ли файл изображением."""
        return file_path.suffix.lower() in FileService.IMAGE_EXTENSIONS

    @staticmethod
    def get_files(folder_path: Path) -> List[FileInfo]:
        """Возвращает список изображений в папке."""
        if not folder_path.exists():
            return []

        files = []
        for ext in FileService.IMAGE_EXTENSIONS:
            for file_path in folder_path.glob(f"*{ext}"):
                stat = file_path.stat()

                if stat.st_size == 0:
                    continue

                files.append(
                    FileInfo(
                        name=file_path.name,
                        path=file_path,
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime)
                    )
                )
                files.append(FileInfo(
                    name=file_path.name,
                    path=file_path,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime)
                ))
           

        # Сортируем по имени
        files.sort(key=lambda f: f.name.lower())
        return files