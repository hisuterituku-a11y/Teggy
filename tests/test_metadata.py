"""
Тесты для MetadataWriter.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import piexif

from core.metadata import MetadataWriter
from core.exif_cleaner import WINDOWS_RATING_TAG


class TestMetadataWriter(unittest.TestCase):
    """Тесты MetadataWriter."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.jpg"

        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.test_file, 'JPEG')

        self.writer = MetadataWriter()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _read_exif(self, filepath: Path):
        """Читает EXIF из файла."""
        img = Image.open(filepath)
        exif_data = img.info.get('exif')
        if exif_data:
            return piexif.load(exif_data)
        return None

    def _decode_xp(self, value):
        """Декодирует XP-поле (bytes или tuple → строка)."""
        if isinstance(value, tuple):
            value = bytes(value)
        if isinstance(value, bytes):
            return value.decode('utf-16le').rstrip('\x00')
        return value

    def test_write_metadata(self):
        """Проверка записи метаданных."""
        self.writer.set_metadata(
            title="Test Title",
            subject="Test Subject",
            comment="Test Comment",
            artist="Test Artist",
            copyright="Test Copyright",
            rating=5,
            keywords="test;keywords"
        )

        self.writer.write(self.test_file)

        exif_dict = self._read_exif(self.test_file)
        self.assertIsNotNone(exif_dict)

        saved_title = exif_dict.get('0th', {}).get(piexif.ImageIFD.XPTitle)
        decoded_title = self._decode_xp(saved_title)
        self.assertEqual(decoded_title, "Test Title")

    def test_write_batch(self):
        """Проверка пакетной записи."""
        file2 = Path(self.temp_dir) / "test2.jpg"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(file2, 'JPEG')

        self.writer.set_metadata(title="Batch Test")
        results = self.writer.write_batch([self.test_file, file2])

        self.assertEqual(len(results), 2)
        self.assertTrue(all(results.values()))


if __name__ == "__main__":
    unittest.main()