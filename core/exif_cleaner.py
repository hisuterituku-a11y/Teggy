"""
Безопасная очистка EXIF-данных.

Правила:
1. Читаем старый EXIF
2. Удаляем ВСЁ, кроме явно разрешённых полей (whitelist)
3. Возвращаем очищенный EXIF

ExifCleaner НЕ СОХРАНЯЕТ файлы — это задача metadata.py и converter.py.
"""

from typing import Optional, Set
import piexif

from core.exceptions import CleanerError


# Windows Rating tag (хранится в 0th IFD)
WINDOWS_RATING_TAG = 18246


class ExifCleaner:
    """
    Очиститель EXIF с whitelist-подходом.
    
    Только поля из ALLOWED_FIELDS сохраняются.
    Всё остальное (Software, DateTime, GPS, и т.д.) — удаляется.
    
    НЕ СОХРАНЯЕТ ФАЙЛЫ — только возвращает очищенный EXIF.
    """

    # ✅ РАЗРЕШЁННЫЕ ПОЛЯ (WHITELIST)
    ALLOWED_FIELDS: Set[int] = {
        # 0th IFD — основные теги
        piexif.ImageIFD.Artist,
        piexif.ImageIFD.Copyright,
        piexif.ImageIFD.ImageDescription,
        piexif.ImageIFD.XPTitle,
        piexif.ImageIFD.XPComment,
        piexif.ImageIFD.XPSubject,
        piexif.ImageIFD.XPKeywords,
        piexif.ImageIFD.XPAuthor,
        # Exif IFD
        piexif.ExifIFD.UserComment,
        # Windows Rating (хранится в 0th IFD)
        WINDOWS_RATING_TAG,
    }

    @staticmethod
    def clean(exif_data: Optional[bytes]) -> bytes:
        """
        Очищает EXIF, оставляя только разрешённые поля.
        
        Args:
            exif_data: исходные EXIF-данные (bytes) или None
            
        Returns:
            очищенные EXIF-данные (bytes)
        """
        try:
            if exif_data is None:
                return piexif.dump({'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'thumbnail': None})
            
            exif_dict = piexif.load(exif_data)
            
            # Очищаем 0th IFD
            if '0th' in exif_dict:
                exif_dict['0th'] = {
                    k: v for k, v in exif_dict['0th'].items()
                    if k in ExifCleaner.ALLOWED_FIELDS
                }
            else:
                exif_dict['0th'] = {}
            
            # Очищаем Exif IFD
            if 'Exif' in exif_dict:
                exif_dict['Exif'] = {
                    k: v for k, v in exif_dict['Exif'].items()
                    if k in ExifCleaner.ALLOWED_FIELDS
                }
            else:
                exif_dict['Exif'] = {}
            
            # Полностью удаляем всё лишнее
            exif_dict['GPS'] = {}
            exif_dict['1st'] = {}
            exif_dict['thumbnail'] = None
            
            return piexif.dump(exif_dict)
            
        except Exception as e:
            raise CleanerError(f"Ошибка очистки EXIF: {e}")