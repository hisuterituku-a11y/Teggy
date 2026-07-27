import sys

from PySide6.QtWidgets import QApplication, QPushButton

from core.paths import resource_path
from gui.main_window_templates import MainWindow
from gui.theme.manager import ThemeManager
from gui.utils.plain_paste_filter import PlainPasteFilter


DEFAULT_THEME = "default"


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    plain_paste_filter = PlainPasteFilter(app)
    app.installEventFilter(plain_paste_filter)

    theme_manager = ThemeManager(resource_path("assets", "themes"))
    theme = theme_manager.load(DEFAULT_THEME)
    app.setStyleSheet(theme.qss)

    window = MainWindow(theme_manager)

    for button in window.findChildren(QPushButton):
        if button.text().strip() in {"Шаблоны", "Управление шаблонами"}:
            button.setObjectName("TemplateProminentButton")
            button.setMinimumHeight(40)
            button.style().unpolish(button)
            button.style().polish(button)

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
