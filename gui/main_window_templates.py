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
        "default": "🌙  Тёмная",
        "light": "☀️  Светлая",
        "corporate": "💼  Корпоративная",
        "frogs": "🐸  Лягушки",
        "sakura": "🌸  Сакура",
    }

    THEME_ICON_COLORS = {
        "default": "#A778FF",
        "light": "#7C4DDE",
        "corporate": "#F59E0B",
        "frogs": "#A9D9BC",
        "sakura": "#D9798D",
    }

    SETTINGS_ICON_COLORS = {
        "default": "#FFFFFF",
        "light": "#4C347E",
        "corporate": "#15171B",
        "frogs": "#244C3D",
        "sakura": "#6A3340",
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
                "updates/check_on_startup", True, type=bool,
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
            self.update_service, type(self.update_service),
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

        current_theme = str(self._app_settings.value("appearance/theme", "default"))
        self._apply_icon_theme(current_theme)

    def _build_theme_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setObjectName("ThemeMenu")
        current = str(self._app_settings.value("appearance/theme", "default"))
        names = self.theme_manager.list_themes() if self.theme_manager is not None else ["default"]
        self._theme_actions = []
        for name in names:
            action = QAction(self.THEME_LABELS.get(name, name), menu)
            action.setCheckable(True)
            action.setChecked(name == current)
            action.triggered.connect(
                lambda checked=False, theme_name=name: self._apply_theme(theme_name)
            )
            menu.addAction(action)
            self._theme_actions.append((name, action))
        return menu

    def _show_theme_menu(self) -> None:
        button = self.topbar.theme_button
        self._theme_menu.popup(button.mapToGlobal(button.rect().bottomLeft()))

    def _open_settings(self) -> None:
        self._switch_page(3, "Настройки")
        self.topbar.title.setText("Настройки")

    def _apply_icon_theme(self, theme_name: str) -> None:
        color = self.THEME_ICON_COLORS.get(theme_name, self.THEME_ICON_COLORS["default"])
        settings_color = self.SETTINGS_ICON_COLORS.get(
            theme_name, self.SETTINGS_ICON_COLORS["default"]
        )
        if hasattr(self.sidebar, "set_icon_color"):
            self.sidebar.set_icon_color(color)
        if hasattr(self.topbar, "set_icon_color"):
            self.topbar.set_icon_color(color, settings_color)

    def _apply_theme(self, theme_name: str) -> None:
        if self.theme_manager is None:
            return
        theme = self.theme_manager.load(theme_name)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet("")
            app.processEvents()
            app.setStyleSheet(theme.qss)
            app.processEvents()

        self._apply_icon_theme(theme_name)
        self._app_settings.setValue("appearance/theme", theme_name)
        for name, action in getattr(self, "_theme_actions", []):
            action.setChecked(name == theme_name)
        if hasattr(self.settings_page, "set_selected_theme"):
            self.settings_page.set_selected_theme(theme_name)
