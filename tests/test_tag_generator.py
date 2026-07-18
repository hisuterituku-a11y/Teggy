from core.tag_generator import TagGenerator

class TestTagGenerator:
    def test_translit(self):
        assert TagGenerator.translit('Лечение зубов') == 'lechenie-zubov'
        assert TagGenerator.translit('Стоматология') == 'stomatologiya'
    
    def test_generate_tags(self):
        services = ['Стоматология', 'Лечение зубов']
        tags = TagGenerator.generate_tags(services)
        assert len(tags) == 2
        assert tags[0] == 'Стоматология;stomatologiya'
