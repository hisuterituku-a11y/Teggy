import logging
import platform
import sys

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from core.logger import setup_logging
from core.paths import resource_path
from core.version import display_version
from gui.dialogs.themed_message_box import ThemedMessageBox
from gui.main_window_templates import MainWindow
from gui.theme.manager import ThemeManager
from gui.utils.plain_paste_filter import PlainPasteFilter


DEFAULT_THEME = "default"
logger = logging.getLogger(__name__)


def _install_themed_message_boxes() -> None:
    QMessageBox.warning = staticmethod(ThemedMessageBox.warning)
    QMessageBox.critical = staticmethod(ThemedMessageBox.critical)

    def themed_question(parent, title, text, buttons=None, default_button=None):
        default = default_button or QMessageBox.StandardButton.No
        return ThemedMessageBox.question(parent, title, text, default)

    QMessageBox.question = staticmethod(themed_question)


def main() -> int:
    log_path = setup_logging()
    logger.info("===== SESSION START =====")
    logger.info("Версия: %s", display_version())
    logger.info("Журнал: %s", log_path)
    logger.info("Исполняемый файл: %s", sys.executable)
    logger.info("Рабочая папка: %s", __import__("pathlib").Path.cwd())
    logger.info("ОС: %s", platform.platform())
    logger.info("Python: %s", sys.version.replace("\n", " "))
    logger.info("Архитектура: %s", platform.machine() or "не определена")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    _install_themed_message_boxes()

    plain_paste_filter = PlainPasteFilter(app)
    app.installEventFilter(plain_paste_filter)

    settings = QSettings("Teggy", "Teggy")
    selected_theme = str(settings.value("appearance/theme", DEFAULT_THEME))
    logger.info("Загрузка темы интерфейса: %s", selected_theme)

    theme_manager = ThemeManager(resource_path("assets", "themes"))
    if selected_theme not in theme_manager.list_themes():
        selected_theme = DEFAULT_THEME
        settings.setValue("appearance/theme", selected_theme)
        logger.warning("Неизвестная тема заменена на стандартную")

    theme = theme_manager.load(selected_theme)
    app.setStyleSheet(theme.qss)

    logger.info("Создание главного окна")
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
    logger.info("Главное окно показано")
    exit_code = app.exec()
    logger.info("Завершение Teggy с кодом %s", exit_code)
    logger.info("===== SESSION END =====")
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logger.exception("Необработанная ошибка при запуске Teggy")
        raise
