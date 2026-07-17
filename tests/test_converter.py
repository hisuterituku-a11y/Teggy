"""
Тесты для ImageConverter.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image

from core.converter import ImageConverter
from core.exceptions import ConversionError


class TestImageConverter(unittest.TestCase):
    """Тесты ImageConverter."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.webp"
        self.output_dir = Path(self.temp_dir) / "output"

        # Создаём тестовый WebP
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.test_file, 'WEBP')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_convert_webp_to_jpg(self):
        """Проверка конвертации WebP → JPG."""
        result = ImageConverter.convert(self.test_file, self.output_dir)
        self.assertTrue(result.exists())
        self.assertEqual(result.suffix.lower(), '.jpg')

    def test_convert_batch(self):
        """Проверка пакетной конвертации."""
        file1 = self.test_file
        file2 = Path(self.temp_dir) / "test2.webp"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(file2, 'WEBP')

        results = ImageConverter.convert_batch([file1, file2], self.output_dir)
        self.assertEqual(len(results), 2)
        self.assertIsNotNone(results[file1])
        self.assertIsNotNone(results[file2])

    def test_needs_conversion(self):
        """Проверка определения необходимости конвертации."""
        self.assertTrue(ImageConverter.needs_conversion(self.test_file))
        jpg_file = Path(self.temp_dir) / "test.jpg"
        self.assertFalse(ImageConverter.needs_conversion(jpg_file))

    def test_convert_invalid_format(self):
        """Проверка ошибки при неподдерживаемом формате."""
        invalid_file = Path(self.temp_dir) / "test.gif"
        with self.assertRaises(ConversionError):
            ImageConverter.convert(invalid_file)


if __name__ == "__main__":
    unittest.main()