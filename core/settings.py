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

    @classmethod
    def get_theme(cls) -> str:
        """Возвращает последнюю выбранную тему."""
        if not cls.SETTINGS_FILE.exists():
            return "dark"
        
        try:
            with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('theme', 'dark')
        except:
            return "dark"
    
    @classmethod
    def save_theme(cls, theme_name: str):
        """Сохраняет выбранную тему."""
        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {}
            if cls.SETTINGS_FILE.exists():
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data['theme'] = theme_name
            
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
    @classmethod
    def get_window_geometry(cls) -> dict:
        """Возвращает размер и положение окна."""
        if not cls.SETTINGS_FILE.exists():
            return {"x": 100, "y": 100, "width": 1280, "height": 820}
        
        try:
            with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    "x": data.get("window_x", 100),
                    "y": data.get("window_y", 100),
                    "width": data.get("window_width", 1280),
                    "height": data.get("window_height", 820)
                }
        except:
            return {"x": 100, "y": 100, "width": 1280, "height": 820}
    
    @classmethod
    def save_window_geometry(cls, x: int, y: int, width: int, height: int):
        """Сохраняет размер и положение окна."""
        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {}
            if cls.SETTINGS_FILE.exists():
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data["window_x"] = x
            data["window_y"] = y
            data["window_width"] = width
            data["window_height"] = height
            
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    @classmethod
    def get_delete_original(cls) -> bool:
        """Возвращает состояние чекбокса 'Удалить оригиналы'."""
        if not cls.SETTINGS_FILE.exists():
            return False
        
        try:
            with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("delete_original", False)
        except:
            return False
    
    @classmethod
    def save_delete_original(cls, value: bool):
        """Сохраняет состояние чекбокса 'Удалить оригиналы'."""
        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {}
            if cls.SETTINGS_FILE.exists():
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data["delete_original"] = value
            
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    @classmethod
    def get_last_template(cls) -> str:
        """Возвращает последний выбранный шаблон."""
        if not cls.SETTINGS_FILE.exists():
            return ""
        
        try:
            with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("last_template", "")
        except:
            return ""
    
    @classmethod
    def save_last_template(cls, template_name: str):
        """Сохраняет последний выбранный шаблон."""
        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {}
            if cls.SETTINGS_FILE.exists():
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data["last_template"] = template_name
            
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass