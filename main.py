import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.theme.manager import ThemeManager


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Создаём менеджер тем один раз
    from core.paths import resource_path

    theme_manager = ThemeManager(
        resource_path("assets", "themes")
    )
    
    # Загружаем последнюю тему из настроек
    from core.settings import Settings
    last_theme = "default"
    theme = theme_manager.load(last_theme)

    print("THEME:", last_theme)
    print("QSS LENGTH:", len(theme.qss))
    print(theme.qss[:300])

    app.setStyleSheet(theme.qss)
    
    
    window = MainWindow(theme_manager)
    window.show()
    sys.exit(app.exec())
   