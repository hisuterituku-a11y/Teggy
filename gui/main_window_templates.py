from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu

import gui.main_window as base_main_window
from gui.pages.settings_page import SettingsPage
from gui.pages.tagging_templates import TaggingPage
from gui.pages.yandex_maps_templates import YandexMapsPage


class MainWindow(base_main_window.MainWindow):
    """MainWindow с едиными шаблонами, настройками и переключаемыми темами."""

    THEME_LABELS = {
        "default": "Тёмная",
        "blue": "Синяя",
        "purple": "Фиолетовая",
        "light": "Светлая",
    }

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

        self.topbar.theme_button.setToolTip("Выбрать тему")
        self.topbar.notify_button.setToolTip("Проверить обновления Teggy")
        self.topbar.settings_button.setToolTip("Настройки")

        self._theme_menu = self._build_theme_menu()
        self.topbar.theme_button.clicked.connect(self._show_theme_menu)
        self.topbar.settings_button.clicked.connect(self._open_settings)
        self.topbar.notify_button.clicked.connect(self._start_manual_update_check)

        self.settings_page.theme_changed.connect(self._apply_theme)
        self.settings_page.check_updates_requested.connect(self._start_manual_update_check)

    def _build_theme_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setObjectName("ThemeMenu")
        group = []
        current = str(self._app_settings.value("appearance/theme", "default"))
        names = self.theme_manager.list_themes() if self.theme_manager is not None else ["default"]
        for name in names:
            action = QAction(self.THEME_LABELS.get(name, name), menu)
            action.setCheckable(True)
            action.setChecked(name == current)
            action.triggered.connect(lambda checked=False, theme_name=name: self._apply_theme(theme_name))
            menu.addAction(action)
            group.append((name, action))
        self._theme_actions = group
        return menu

    def _show_theme_menu(self) -> None:
        button = self.topbar.theme_button
        point = button.mapToGlobal(button.rect().bottomLeft())
        self._theme_menu.popup(point)

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
        for name, action in getattr(self, "_theme_actions", []):
            action.setChecked(name == theme_name)
        if hasattr(self.settings_page, "set_selected_theme"):
            self.settings_page.set_selected_theme(theme_name)
