from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

import gui.main_window as base_main_window
from gui.pages.settings_page import SettingsPage
from gui.pages.tagging_templates import TaggingPage
from gui.pages.yandex_maps_templates import YandexMapsPage


class MainWindow(base_main_window.MainWindow):
    """MainWindow с едиными шаблонами, настройками и переключаемыми темами."""

    def __init__(self, theme_manager=None):
        self._app_settings = QSettings("Teggy", "Teggy")
        base_main_window.TaggingPage = TaggingPage
        base_main_window.YandexMapsPage = YandexMapsPage
        base_main_window.SettingsPage = lambda: SettingsPage(
            theme_manager.list_themes() if theme_manager is not None else ["default"]
        )

        original_update_check = base_main_window.UpdateService.check

        def startup_aware_check(service) -> bool:
            enabled = self._app_settings.value(
                "updates/check_on_startup",
                True,
                type=bool,
            )
            if not enabled:
                return False
            return original_update_check(service)

        base_main_window.UpdateService.check = startup_aware_check
        try:
            super().__init__(theme_manager)
        finally:
            base_main_window.UpdateService.check = original_update_check

        self.update_service.check = original_update_check.__get__(
            self.update_service,
            type(self.update_service),
        )

        self.topbar.theme_button.setToolTip("Оформление")
        self.topbar.notify_button.setToolTip("Проверить обновления Teggy")
        self.topbar.settings_button.setToolTip("Настройки")

        self.topbar.theme_button.clicked.connect(self._open_settings)
        self.topbar.settings_button.clicked.connect(self._open_settings)
        self.topbar.notify_button.clicked.connect(self._start_manual_update_check)

        self.settings_page.theme_changed.connect(self._apply_theme)
        self.settings_page.check_updates_requested.connect(self._start_manual_update_check)

    def _open_settings(self) -> None:
        self._switch_page(3, "Настройки")
        self.topbar.title.setText("Настройки")

    def _apply_theme(self, theme_name: str) -> None:
        if self.theme_manager is None:
            return
        theme = self.theme_manager.load(theme_name)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.qss)
            app.processEvents()
        self._app_settings.setValue("appearance/theme", theme_name)
