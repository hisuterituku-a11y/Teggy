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

        self.topbar.theme_button.setToolTip("Тема оформления")
        self.topbar.notify_button.setToolTip("Уведомления и обновления Teggy")
        self.topbar.settings_button.setToolTip("Настройки")

        self.topbar.theme_button.clicked.connect(self._open_settings)
        self.topbar.settings_button.clicked.connect(self._open_settings)
        self.topbar.notify_button.clicked.connect(self._open_updates)

    def _open_settings(self) -> None:
        self._switch_page(3, "Настройки")
        self.topbar.title.setText("Настройки")

    def _open_updates(self) -> None:
        self._switch_page(0, "Главная")
        self.topbar.title.setText("Главная")
        self._start_manual_update_check()
