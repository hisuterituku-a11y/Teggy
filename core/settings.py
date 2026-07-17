import json
from pathlib import Path

class Settings:
    """Управление настройками приложения."""
    
    SETTINGS_FILE = Path.home() / ".teggy" / "settings.json"
    
    @classmethod
    def get_last_folder(cls) -> str:
        """Возвращает последнюю открытую папку."""
        if not cls.SETTINGS_FILE.exists():
            return ""
        
        try:
            with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('last_folder', '')
        except:
            return ""
    
    @classmethod
    def save_last_folder(cls, folder_path: str):
        """Сохраняет последнюю открытую папку."""
        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {}
            if cls.SETTINGS_FILE.exists():
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data['last_folder'] = folder_path
            
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass