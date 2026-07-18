"""
Запись метаданных в изображения.

Перед записью:
1. Очищает старый EXIF через ExifCleaner
2. Создаёт новый EXIF с разрешёнными полями
3. Записывает в файл
"""

from pathlib import Path
from typing import Dict, Optional
from PIL import Image
import piexif

from core.exceptions import MetadataError
from core.exif_cleaner import ExifCleaner, WINDOWS_RATING_TAG


class MetadataWriter:
    """
    Записывает метаданные в изображение.
    
    Особенности:
    - XP-поля (Title, Subject, Comment, Keywords, Author) кодируются в UTF-16LE
    - Обычные поля (Artist, Copyright, ImageDescription) — в UTF-8
    - Рейтинг Windows сохраняется как число (1, 25, 50, 75, 99)
    """

    def __init__(self):
        self.title = ""
        self.subject = ""
        self.comment = ""
        self.artist = ""
        self.copyright = ""
        self.rating = 5
        self.keywords = ""

    def set_metadata(self, **kwargs) -> None:
        """
        Устанавливает метаданные для записи.

        Args:
            title: название (строка)
            subject: тема (строка)
            comment: комментарий (строка)
            artist: автор (строка)
            copyright: авторские права (строка)
            rating: рейтинг 1-5 (число)
            keywords: ключевые слова (строка)
        """
        if "title" in kwargs:
            self.title = kwargs["title"]
        if "subject" in kwargs:
            self.subject = kwargs["subject"]
        if "comment" in kwargs:
            self.comment = kwargs["comment"]
        if "artist" in kwargs:
            self.artist = kwargs["artist"]
        if "copyright" in kwargs:
            self.copyright = kwargs["copyright"]
        if "rating" in kwargs:
            self.rating = min(max(kwargs["rating"], 1), 5)
        if "keywords" in kwargs:
            self.keywords = kwargs["keywords"]

    def _encode_xp(self, value: str) -> bytes:
        """
        Кодирует строку в формат Windows XP (UTF-16LE).
        
        Windows XP-поля (XPTitle, XPSubject, XPComment, XPKeywords, XPAuthor)
        хранятся в кодировке UTF-16LE.
        """
        if not value:
            return b''
        return value.encode('utf-16le')

    def write(self, filepath: Path) -> bool:
        """
        Записывает метаданные в файл.

        Args:
            filepath: путь к файлу

        Returns:
            True если успешно

        Raises:
            MetadataError: если не удалось записать
        """
        try:
            # Проверяем, что файл существует
            if not filepath.exists():
                raise MetadataError(f"Файл не найден: {filepath}")

            # Открываем изображение
            img = Image.open(filepath)

            # Получаем текущий EXIF и очищаем его
            exif_data = img.info.get('exif')
            cleaned_exif = ExifCleaner.clean(exif_data)

            # Загружаем очищенный EXIF в словарь
            exif_dict = piexif.load(cleaned_exif)

            # === ЗАПОЛНЯЕМ 0th IFD ===
            if '0th' not in exif_dict:
                exif_dict['0th'] = {}

            # Windows XP-поля (UTF-16LE)
            if self.title:
                exif_dict['0th'][piexif.ImageIFD.XPTitle] = self._encode_xp(self.title)
            if self.subject:
                exif_dict['0th'][piexif.ImageIFD.XPSubject] = self._encode_xp(self.subject)
            if self.comment:
                exif_dict['0th'][piexif.ImageIFD.XPComment] = self._encode_xp(self.comment)
            if self.keywords:
                exif_dict['0th'][piexif.ImageIFD.XPKeywords] = self._encode_xp(self.keywords)
            if self.artist:
                exif_dict['0th'][piexif.ImageIFD.XPAuthor] = self._encode_xp(self.artist)

            # Обычные EXIF-поля (UTF-8)
            if self.artist:
                exif_dict['0th'][piexif.ImageIFD.Artist] = self.artist.encode('utf-8')
            if self.copyright:
                exif_dict['0th'][piexif.ImageIFD.Copyright] = self.copyright.encode('utf-8')
            if self.subject:
                exif_dict['0th'][piexif.ImageIFD.ImageDescription] = self.subject.encode('utf-8')

            # === ЗАПОЛНЯЕМ Exif IFD ===
            if 'Exif' not in exif_dict:
                exif_dict['Exif'] = {}

            if self.comment:
                exif_dict['Exif'][piexif.ExifIFD.UserComment] = self.comment.encode('utf-8')

            # === РЕЙТИНГ (Windows) ===
            rating_map = {1: 1, 2: 25, 3: 50, 4: 75, 5: 99}
            exif_dict['0th'][WINDOWS_RATING_TAG] = rating_map.get(self.rating, 99)

            # Конвертируем в bytes и сохраняем
            exif_bytes = piexif.dump(exif_dict)
            img.save(filepath, format='JPEG', exif=exif_bytes, quality=95)

            return True

        except Exception as e:
            raise MetadataError(f"Ошибка записи метаданных в {filepath.name}: {e}")

    def write_batch(self, filepaths: list) -> Dict[str, bool]:
        """
        Записывает метаданные в несколько файлов.

        Args:
            filepaths: список путей к файлам

        Returns:
            словарь {файл: статус}
        """
        results = {}
        for filepath in filepaths:
            try:
                self.write(Path(filepath))
                results[str(filepath)] = True
            except MetadataError:
                results[str(filepath)] = False
        return results