import pytest
from pathlib import Path
from core.files.file_service import FileService, FileInfo

class TestFileService:
    def test_get_files_returns_images_only(self, test_images):
        files = FileService.get_files(test_images)
        assert len(files) == 5
        extensions = [f.extension for f in files]
        assert '.jpg' in extensions
        assert '.png' in extensions
        assert '.webp' in extensions
        assert '.bmp' in extensions
        assert '.tiff' in extensions
    
    def test_get_files_returns_file_info(self, test_images):
        files = FileService.get_files(test_images)
        for f in files:
            assert isinstance(f, FileInfo)
            assert f.name
            assert f.path.exists()
            assert f.size > 0
            assert f.extension in FileService.IMAGE_EXTENSIONS
    
    def test_is_image(self, test_images):
        assert FileService.is_image(test_images / 'test.jpg')
        assert FileService.is_image(test_images / 'test.png')
        assert not FileService.is_image(test_images / 'test.txt')
