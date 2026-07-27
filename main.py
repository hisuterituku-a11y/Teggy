import sys

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from core.paths import resource_path
from gui.dialogs.themed_message_box import ThemedMessageBox
from gui.main_window_templates import MainWindow
from gui.theme.manager import ThemeManager
from gui.utils.plain_paste_filter import PlainPasteFilter


DEFAULT_THEME = "default"


def _install_themed_message_boxes() -> None:
    QMessageBox.warning = staticmethod(ThemedMessageBox.warning)
    QMessageBox.critical = staticmethod(ThemedMessageBox.critical)

    def themed_question(parent, title, text, buttons=None, default_button=None):
        default = default_button or QMessageBox.StandardButton.No
        return ThemedMessageBox.question(parent, title, text, default)

    QMessageBox.question = staticmethod(themed_question)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    _install_themed_message_boxes()

    plain_paste_filter = PlainPasteFilter(app)
    app.installEventFilter(plain_paste_filter)

    settings = QSettings("Teggy", "Teggy")
    selected_theme = str(settings.value("appearance/theme", DEFAULT_THEME))

    theme_manager = ThemeManager(resource_path("assets", "themes"))
    if selected_theme not in theme_manager.list_themes():
        selected_theme = DEFAULT_THEME
        settings.setValue("appearance/theme", selected_theme)

    theme = theme_manager.load(selected_theme)
    app.setStyleSheet(theme.qss)

    window = MainWindow(theme_manager)
    window.reset_interface_geometry()

    for button in window.findChildren(QPushButton):
        if button.text().strip() in {
            "Шаблоны",
            "Управление шаблонами",
            "✦ Шаблоны метаданных",
        }:
            button.setObjectName("TemplateProminentButton")
            button.setMinimumHeight(40)
            button.style().unpolish(button)
            button.style().polish(button)

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
