from __future__ import annotations

import gui.main_window as base_main_window
from gui.pages.tagging_templates import TaggingPage
from gui.pages.yandex_maps_templates import YandexMapsPage


class MainWindow(base_main_window.MainWindow):
    """MainWindow с едиными шаблонами и компактной навигацией."""

    def __init__(self, theme_manager=None):
        base_main_window.TaggingPage = TaggingPage
        base_main_window.YandexMapsPage = YandexMapsPage
        super().__init__(theme_manager)

        self.topbar.theme_button.setToolTip("Настройки темы")
        self.topbar.notify_button.setToolTip("Настройки уведомлений")
        self.topbar.theme_button.clicked.connect(self._open_settings)
        self.topbar.notify_button.clicked.connect(self._open_settings)

    def _open_settings(self) -> None:
        self._switch_page(3, "Настройки")
        self.topbar.title.setText("Настройки")
