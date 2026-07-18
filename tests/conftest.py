import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image

@pytest.fixture
def temp_dir():
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)

@pytest.fixture
def test_images(temp_dir):
    img = Image.new('RGB', (100, 100), color='red')
    img.save(temp_dir / 'test.jpg', 'JPEG', quality=95)
    
    img = Image.new('RGBA', (100, 100), color=(0, 255, 0, 128))
    img.save(temp_dir / 'test.png', 'PNG')
    
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(temp_dir / 'test.webp', 'WebP', quality=95)
    
    img = Image.new('RGB', (100, 100), color='yellow')
    img.save(temp_dir / 'test.bmp', 'BMP')
    
    img = Image.new('RGB', (100, 100), color='purple')
    img.save(temp_dir / 'test.tiff', 'TIFF')
    
    (temp_dir / 'test.txt').write_text('test')
    return temp_dir

@pytest.fixture
def sample_metadata():
    return {
        'title': 'Test Title',
        'subject': 'Test Subject',
        'artist': 'Test Artist',
        'keywords': ['tag1', 'tag2'],
        'comment': 'Test Comment',
        'copyright': 'Test Copyright'
    }
