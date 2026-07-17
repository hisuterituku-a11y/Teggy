import piexif
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image


class MetadataService:
    """Сервис для работы с метаданными изображений."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg'}
    
    @staticmethod
    def can_read(file_path: str) -> bool:
        """Проверяет, можно ли читать метаданные из файла."""
        ext = Path(file_path).suffix.lower()
        return ext in MetadataService.SUPPORTED_FORMATS
    
    @staticmethod
    def can_write(file_path: str) -> bool:
        """Проверяет, можно ли записывать метаданные в файл."""
        ext = Path(file_path).suffix.lower()
        return ext in MetadataService.SUPPORTED_FORMATS
    
    @staticmethod
    def read_metadata(file_path: str) -> Dict[str, Any]:
        """
        Читает метаданные из JPG-файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Dict: Словарь с метаданными
        """
        if not MetadataService.can_read(file_path):
            return {}
        
        try:
            img = Image.open(file_path)
            exif_data = img.info.get('exif')
            
            if not exif_data:
                return {}
            
            exif_dict = piexif.load(exif_data)
            result = {}
            
            # Читаем 0th IFD
            if '0th' in exif_dict:
                zeroth = exif_dict['0th']
                
                # Artist
                if piexif.ImageIFD.Artist in zeroth:
                    result['artist'] = zeroth[piexif.ImageIFD.Artist].decode('utf-8', errors='ignore')
                
                # Copyright
                if piexif.ImageIFD.Copyright in zeroth:
                    result['copyright'] = zeroth[piexif.ImageIFD.Copyright].decode('utf-8', errors='ignore')
                
                # XP Title (Windows)
                if piexif.ImageIFD.XPTitle in zeroth:
                    result['title'] = zeroth[piexif.ImageIFD.XPTitle].decode('utf-16le', errors='ignore').strip('\x00')
                
                # XP Subject (Windows)
                if piexif.ImageIFD.XPSubject in zeroth:
                    result['subject'] = zeroth[piexif.ImageIFD.XPSubject].decode('utf-16le', errors='ignore').strip('\x00')
                
                # XP Keywords (Windows)
                if piexif.ImageIFD.XPKeywords in zeroth:
                    keywords = zeroth[piexif.ImageIFD.XPKeywords].decode('utf-16le', errors='ignore').strip('\x00')
                    # Разбиваем по точке с запятой или запятой
                    if ';' in keywords:
                        result['keywords'] = [k.strip() for k in keywords.split(';') if k.strip()]
                    elif ',' in keywords:
                        result['keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
                    else:
                        result['keywords'] = [keywords] if keywords else []
                
                # XP Comment (Windows)
                if piexif.ImageIFD.XPComment in zeroth:
                    result['comment'] = zeroth[piexif.ImageIFD.XPComment].decode('utf-16le', errors='ignore').strip('\x00')
                
                # ImageDescription (стандартное поле Description)
                if piexif.ImageIFD.ImageDescription in zeroth:
                    result['description'] = zeroth[piexif.ImageIFD.ImageDescription].decode('utf-8', errors='ignore')
            
            # Читаем Exif IFD
            if 'Exif' in exif_dict:
                exif = exif_dict['Exif']
                
                # UserComment
                if piexif.ExifIFD.UserComment in exif:
                    comment = exif[piexif.ExifIFD.UserComment]
                    # Удаляем префикс кодировки (обычно ASCII)
                    if isinstance(comment, bytes):
                        try:
                            result['comment'] = comment.decode('utf-8', errors='ignore')
                        except:
                            result['comment'] = comment.decode('ascii', errors='ignore')
                
                # Rating (Windows)
                if piexif.ExifIFD.Rating in exif:
                    rating_value = exif[piexif.ExifIFD.Rating]
                    # Маппинг Windows: 1→1, 25→2, 50→3, 75→4, 99→5
                    rating_map = {1: 1, 25: 2, 50: 3, 75: 4, 99: 5}
                    result['rating'] = rating_map.get(rating_value, 0)
            
            return result
            
        except Exception as e:
            # Возвращаем пустой словарь в случае ошибки
            return {}
    
    @staticmethod
    def get_format_info(file_path: str) -> Dict[str, Any]:
        """
        Возвращает информацию о формате файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Dict: Информация о формате
        """
        ext = Path(file_path).suffix.lower()
        
        can_read = MetadataService.can_read(file_path)
        can_write = MetadataService.can_write(file_path)
        
        format_names = {
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.png': 'PNG',
            '.webp': 'WebP',
            '.tif': 'TIFF',
            '.tiff': 'TIFF',
            '.bmp': 'BMP',
        }
        
        return {
            'format': format_names.get(ext, ext.upper()),
            'extension': ext,
            'can_read_metadata': can_read,
            'can_write_metadata': can_write,
            'needs_conversion': not can_write,
            'is_jpg': ext in {'.jpg', '.jpeg'}
        }