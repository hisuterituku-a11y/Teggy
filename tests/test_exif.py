"""
Тесты для EXIF-очистителя.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import piexif

from core.exif_cleaner import ExifCleaner, WINDOWS_RATING_TAG


class TestExifCleaner(unittest.TestCase):
    """Тесты ExifCleaner."""

    def setUp(self):
        """Создаём временный JPG для тестов."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.jpg"

        # Создаём тестовое изображение
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.test_file, 'JPEG')

    def tearDown(self):
        """Удаляем временные файлы."""
        shutil.rmtree(self.temp_dir)

    def _write_exif(self, filepath: Path, exif_dict: dict):
        """Записывает EXIF в файл."""
        img = Image.open(filepath)
        exif_bytes = piexif.dump(exif_dict)
        img.save(filepath, 'JPEG', exif=exif_bytes)

    def _decode_xp_keywords(self, value):
        """Декодирует XPKeywords из bytes или tuple в строку."""
        if isinstance(value, tuple):
            value = bytes(value)
        if isinstance(value, bytes):
            # XP поля в Windows хранятся в UTF-16LE с нулевыми байтами в конце
            decoded = value.decode('utf-16le')
            # Убираем нулевые символы в конце
            return decoded.rstrip('\x00')
        return str(value)

    def test_clean_removes_software(self):
        """Проверка: поле Software должно удаляться."""
        exif_dict = {
            '0th': {piexif.ImageIFD.Software: b'TestApp'},
            'Exif': {},
            'GPS': {},
            '1st': {},
            'thumbnail': None
        }
        self._write_exif(self.test_file, exif_dict)

        img = Image.open(self.test_file)
        cleaned = ExifCleaner.clean(img.info.get('exif'))
        cleaned_dict = piexif.load(cleaned)
        self.assertNotIn(piexif.ImageIFD.Software, cleaned_dict.get('0th', {}))

    def test_clean_removes_datetime(self):
        """Проверка: поле DateTime должно удаляться."""
        exif_dict = {
            '0th': {piexif.ImageIFD.DateTime: b'2024:01:01 12:00:00'},
            'Exif': {},
            'GPS': {},
            '1st': {},
            'thumbnail': None
        }
        self._write_exif(self.test_file, exif_dict)

        img = Image.open(self.test_file)
        cleaned = ExifCleaner.clean(img.info.get('exif'))
        cleaned_dict = piexif.load(cleaned)
        self.assertNotIn(piexif.ImageIFD.DateTime, cleaned_dict.get('0th', {}))

    def test_clean_preserves_allowed_fields(self):
        """Проверка: разрешённые поля сохраняются."""
        test_keywords = 'keyword1;keyword2'

        exif_dict = {
            '0th': {
                piexif.ImageIFD.Artist: b'Test Artist',
                piexif.ImageIFD.Copyright: b'Test Copyright',
                piexif.ImageIFD.XPKeywords: test_keywords.encode('utf-16le'),
            },
            'Exif': {},
            'GPS': {},
            '1st': {},
            'thumbnail': None
        }
        self._write_exif(self.test_file, exif_dict)

        img = Image.open(self.test_file)
        cleaned = ExifCleaner.clean(img.info.get('exif'))
        cleaned_dict = piexif.load(cleaned)

        self.assertEqual(
            cleaned_dict.get('0th', {}).get(piexif.ImageIFD.Artist),
            b'Test Artist'
        )
        self.assertEqual(
            cleaned_dict.get('0th', {}).get(piexif.ImageIFD.Copyright),
            b'Test Copyright'
        )

        saved_keywords = cleaned_dict.get('0th', {}).get(piexif.ImageIFD.XPKeywords)
        self.assertIsNotNone(saved_keywords)
        decoded = self._decode_xp_keywords(saved_keywords)
        self.assertEqual(decoded, test_keywords)

    def test_clean_preserves_xp_keywords(self):
        """Проверка: XPKeywords сохраняются."""
        test_keywords = 'implantaciya;lechenie;protezirovanie'

        exif_dict = {
            '0th': {
                piexif.ImageIFD.XPKeywords: test_keywords.encode('utf-16le'),
            },
            'Exif': {},
            'GPS': {},
            '1st': {},
            'thumbnail': None
        }
        self._write_exif(self.test_file, exif_dict)

        img = Image.open(self.test_file)
        cleaned = ExifCleaner.clean(img.info.get('exif'))
        cleaned_dict = piexif.load(cleaned)

        saved_keywords = cleaned_dict.get('0th', {}).get(piexif.ImageIFD.XPKeywords)
        self.assertIsNotNone(saved_keywords)
        decoded = self._decode_xp_keywords(saved_keywords)
        self.assertEqual(decoded, test_keywords)

    def test_clean_preserves_rating(self):
        """Проверка: Windows Rating сохраняется."""
        exif_dict = {
            '0th': {
                WINDOWS_RATING_TAG: 99,
            },
            'Exif': {},
            'GPS': {},
            '1st': {},
            'thumbnail': None
        }
        self._write_exif(self.test_file, exif_dict)

        img = Image.open(self.test_file)
        cleaned = ExifCleaner.clean(img.info.get('exif'))
        cleaned_dict = piexif.load(cleaned)
        self.assertEqual(
            cleaned_dict.get('0th', {}).get(WINDOWS_RATING_TAG),
            99
        )

    def test_clean_empty_exif(self):
        """Проверка: если EXIF нет — ошибки не должно быть."""
        img = Image.open(self.test_file)
        img.save(self.test_file, 'JPEG', exif=b'')

        img = Image.open(self.test_file)
        cleaned = ExifCleaner.clean(img.info.get('exif'))

        self.assertIsInstance(cleaned, bytes)
        cleaned_dict = piexif.load(cleaned)
        self.assertIn('0th', cleaned_dict)


if __name__ == "__main__":
    unittest.main()