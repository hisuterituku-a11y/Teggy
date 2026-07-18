import pytest
from pathlib import Path
from core.converter import ImageConverter
from core.exceptions import ConversionError

class TestImageConverter:
    def test_convert_png_to_jpg(self, test_images):
        png_path = test_images / 'test.png'
        result = ImageConverter.convert(png_path)
        assert result.exists()
        assert result.suffix.lower() == '.jpg'
    
    def test_needs_conversion(self, test_images):
        assert ImageConverter.needs_conversion(test_images / 'test.png')
        assert not ImageConverter.needs_conversion(test_images / 'test.jpg')
    
    def test_convert_batch(self, test_images, temp_dir):
        paths = [test_images / 'test.png', test_images / 'test.webp']
        results = ImageConverter.convert_batch(paths, output_dir=temp_dir)
        assert len(results) == 2
        for original, new in results.items():
            assert new is not None
            assert new.exists()
