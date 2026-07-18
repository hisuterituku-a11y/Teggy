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
        """Читает метаданные из JPG-файла."""
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
                    xp_title = zeroth[piexif.ImageIFD.XPTitle]
                    if isinstance(xp_title, tuple):
                        xp_title = bytes(xp_title)
                    result['title'] = xp_title.decode('utf-16le', errors='ignore').strip('\x00')
                
                # XP Subject (Windows)
                if piexif.ImageIFD.XPSubject in zeroth:
                    xp_subject = zeroth[piexif.ImageIFD.XPSubject]
                    if isinstance(xp_subject, tuple):
                        xp_subject = bytes(xp_subject)
                    result['subject'] = xp_subject.decode('utf-16le', errors='ignore').strip('\x00')
                
                # XP Keywords (Windows)
                if piexif.ImageIFD.XPKeywords in zeroth:
                    xp_keywords = zeroth[piexif.ImageIFD.XPKeywords]
                    if isinstance(xp_keywords, tuple):
                        xp_keywords = bytes(xp_keywords)
                    keywords = xp_keywords.decode('utf-16le', errors='ignore').strip('\x00')
                    if ';' in keywords:
                        result['keywords'] = [k.strip() for k in keywords.split(';') if k.strip()]
                    elif ',' in keywords:
                        result['keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
                    else:
                        result['keywords'] = [keywords] if keywords else []
                
                # XP Comment (Windows)
                if piexif.ImageIFD.XPComment in zeroth:
                    xp_comment = zeroth[piexif.ImageIFD.XPComment]
                    if isinstance(xp_comment, tuple):
                        xp_comment = bytes(xp_comment)
                    result['comment'] = xp_comment.decode('utf-16le', errors='ignore').strip('\x00')
                
                # ImageDescription
                if piexif.ImageIFD.ImageDescription in zeroth:
                    result['description'] = zeroth[piexif.ImageIFD.ImageDescription].decode('utf-8', errors='ignore')
            
                    # Читаем Exif IFD
                if 'Exif' in exif_dict:
                    exif = exif_dict['Exif']
                    
                    # UserComment
                    if piexif.ExifIFD.UserComment in exif:
                        comment = exif[piexif.ExifIFD.UserComment]
                        if isinstance(comment, bytes):
                            try:
                                result['comment'] = comment.decode('utf-8', errors='ignore')
                            except:
                                result['comment'] = comment.decode('ascii', errors='ignore')
                    
                    # Rating (Windows) — используем числовой тег
                    rating_tag = 18246
                    if rating_tag in exif:
                        rating_value = exif[rating_tag]
                        rating_map = {1: 1, 25: 2, 50: 3, 75: 4, 99: 5}
                        result['rating'] = rating_map.get(rating_value, 0)
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {}
    
    @staticmethod
    def get_format_info(file_path: str) -> Dict[str, Any]:
        """Возвращает информацию о формате файла."""
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

    @staticmethod
    def write_metadata(file_path: str, metadata: dict) -> bool:
        """Записывает метаданные в JPG-файл."""
        if not MetadataService.can_write(file_path):
            return False

        try:
            img = Image.open(file_path)
            exif_dict = {'0th': {}, 'Exif': {}}

            # Название
            if 'title' in metadata and metadata['title']:
                exif_dict['0th'][piexif.ImageIFD.XPTitle] = metadata['title'].encode('utf-16le')

            # Тема
            if 'subject' in metadata and metadata['subject']:
                exif_dict['0th'][piexif.ImageIFD.XPSubject] = metadata['subject'].encode('utf-16le')
                exif_dict['0th'][piexif.ImageIFD.ImageDescription] = metadata['subject'].encode('utf-8')

            # Автор
            if 'artist' in metadata and metadata['artist']:
                exif_dict['0th'][piexif.ImageIFD.Artist] = metadata['artist'].encode('utf-8')
                exif_dict['0th'][piexif.ImageIFD.XPAuthor] = metadata['artist'].encode('utf-16le')

            # Теги (keywords)
            if 'keywords' in metadata and metadata['keywords']:
                if isinstance(metadata['keywords'], list):
                    keywords_str = '; '.join(metadata['keywords'])
                else:
                    keywords_str = metadata['keywords']
                exif_dict['0th'][piexif.ImageIFD.XPKeywords] = keywords_str.encode('utf-16le')

            # Комментарий
            if 'comment' in metadata and metadata['comment']:
                exif_dict['0th'][piexif.ImageIFD.XPComment] = metadata['comment'].encode('utf-16le')
                exif_dict['Exif'][piexif.ExifIFD.UserComment] = metadata['comment'].encode('utf-8')

            # Авторские права
            if 'copyright' in metadata and metadata['copyright']:
                exif_dict['0th'][piexif.ImageIFD.Copyright] = metadata['copyright'].encode('utf-8')

            # Рейтинг всегда 5 (Windows: 99)
            exif_dict['0th'][18246] = 99  # Rating (Windows)

            # Дата
            from datetime import datetime
            now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
            exif_dict['0th'][piexif.ImageIFD.DateTime] = now.encode('utf-8')

            exif_bytes = piexif.dump(exif_dict)
            img.save(file_path, exif=exif_bytes, format='JPEG', quality=95)
            return True

        except Exception as e:
            print(f"Ошибка записи метаданных: {e}")
            return False

    @staticmethod
    def convert_to_jpg(file_path: str, quality: int = 95) -> Optional[str]:
        """Конвертирует изображение в JPG."""
        try:
            img = Image.open(file_path)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            output_path = Path(file_path).with_suffix('.jpg')
            img.save(output_path, 'JPEG', quality=quality)
            return str(output_path)

        except Exception as e:
            print(f"Ошибка конвертации: {e}")
            return None

    @staticmethod
    def process_file(file_path: str, metadata: dict, delete_original: bool = False) -> dict:
        """
        Обрабатывает файл: конвертирует в JPG при необходимости и записывает метаданные.

        Returns:
            dict: {'success': bool, 'output_path': str, 'message': str}
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        # Если не JPG — конвертируем
        if ext not in {'.jpg', '.jpeg'}:
            jpg_path = MetadataService.convert_to_jpg(file_path)
            if not jpg_path:
                return {'success': False, 'output_path': None, 'message': 'Ошибка конвертации'}

            if delete_original:
                try:
                    path.unlink()
                except:
                    pass

            file_path = jpg_path

        # Записываем метаданные
        success = MetadataService.write_metadata(file_path, metadata)
        if not success:
            return {'success': False, 'output_path': file_path, 'message': 'Ошибка записи метаданных'}

        return {'success': True, 'output_path': file_path, 'message': 'Готово'}