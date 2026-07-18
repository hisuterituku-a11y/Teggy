import pytest
from pathlib import Path
from PIL import Image
from core.files.file_service import FileService
from core.metadata.metadata_service import MetadataService
from core.converter import ImageConverter
from core.template_manager import TemplateManager

class TestSmoke:
    def test_full_workflow(self, temp_dir):
        img = Image.new('RGB', (100, 100), color='red')
        img.save(temp_dir / 'test1.jpg', 'JPEG', quality=95)
        img = Image.new('RGBA', (100, 100), color=(0, 255, 0, 128))
        img.save(temp_dir / 'test2.png', 'PNG')
        
        files = FileService.get_files(temp_dir)
        assert len(files) == 2
        
        new_metadata = {
            'title': 'Smoke Test',
            'subject': 'Testing',
            'artist': 'Teggy',
            'keywords': ['test', 'smoke'],
            'comment': 'Test comment',
            'copyright': 'Teggy 2026'
        }
        
        jpg_file = temp_dir / 'test1.jpg'
        success = MetadataService.write_metadata(str(jpg_file), new_metadata)
        assert success
        
        read_meta = MetadataService.read_metadata(str(jpg_file))
        assert read_meta.get('title') == 'Smoke Test'
        
        png_file = temp_dir / 'test2.png'
        jpg_result = ImageConverter.convert(png_file)
        assert jpg_result.exists()
        
        template_name = 'smoke_template'
        template_data = {'name': template_name, 'title': 'Template Test'}
        TemplateManager.save(template_name, template_data)
        loaded = TemplateManager.load(template_name)
        assert loaded['title'] == 'Template Test'
        TemplateManager.delete(template_name)
