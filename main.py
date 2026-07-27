import sys

from PySide6.QtWidgets import QApplication

from core.paths import resource_path
from gui.main_window_templates import MainWindow
from gui.theme.manager import ThemeManager


DEFAULT_THEME = "default"


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    theme_manager = ThemeManager(resource_path("assets", "themes"))
    theme = theme_manager.load(DEFAULT_THEME)
    app.setStyleSheet(theme.qss)

    window = MainWindow(theme_manager)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
