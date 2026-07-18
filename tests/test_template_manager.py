import pytest
from core.template_manager import TemplateManager
from core.exceptions import TemplateError

class TestTemplateManager:
    def test_save_and_load(self):
        name = 'test_template'
        data = {'name': name, 'title': 'Test', 'subject': 'Test'}
        TemplateManager.save(name, data)
        templates = TemplateManager.list_templates()
        assert name in templates
        loaded = TemplateManager.load(name)
        assert loaded['title'] == 'Test'
        TemplateManager.delete(name)
        templates = TemplateManager.list_templates()
        assert name not in templates
    
    def test_load_nonexistent(self):
        with pytest.raises(TemplateError):
            TemplateManager.load('nonexistent_template')
