import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.theme.manager import ThemeManager


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Создаём менеджер тем один раз
    theme_manager = ThemeManager(Path("assets/themes"))
    
    # Загружаем последнюю тему из настроек
    from core.settings import Settings
    last_theme = Settings.get_theme() or "dark"
    theme = theme_manager.load(last_theme)
    app.setStyleSheet(theme.qss)
    
    
    window = MainWindow(theme_manager)
    window.show()
    sys.exit(app.exec())
   