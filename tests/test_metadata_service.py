import pytest
from pathlib import Path
from core.metadata.metadata_service import MetadataService

class TestMetadataService:
    def test_can_read_jpg(self, test_images):
        assert MetadataService.can_read(str(test_images / 'test.jpg'))
        assert not MetadataService.can_read(str(test_images / 'test.png'))
    
    def test_can_write_jpg(self, test_images):
        assert MetadataService.can_write(str(test_images / 'test.jpg'))
        assert not MetadataService.can_write(str(test_images / 'test.png'))
    
    def test_read_write_metadata(self, test_images, sample_metadata):
        file_path = str(test_images / 'test.jpg')
        success = MetadataService.write_metadata(file_path, sample_metadata)
        assert success
        metadata = MetadataService.read_metadata(file_path)
        assert metadata.get('title') == sample_metadata['title']
        assert metadata.get('subject') == sample_metadata['subject']
    
    def test_convert_to_jpg(self, test_images):
        png_path = str(test_images / 'test.png')
        jpg_path = MetadataService.convert_to_jpg(png_path)
        assert jpg_path is not None
        assert Path(jpg_path).exists()
        assert Path(jpg_path).suffix.lower() == '.jpg'
    
    def test_process_file(self, test_images, sample_metadata):
        file_path = str(test_images / 'test.png')
        result = MetadataService.process_file(file_path, sample_metadata)
        assert result['success'] is True
        assert Path(result['output_path']).exists()
