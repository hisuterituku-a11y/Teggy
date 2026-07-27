from __future__ import annotations

import gui.main_window as base_main_window
from gui.pages.tagging_templates import TaggingPage
from gui.pages.yandex_maps_templates import YandexMapsPage


class MainWindow(base_main_window.MainWindow):
    """MainWindow с едиными шаблонами для тегирования и Яндекс Карт."""

    def __init__(self, theme_manager=None):
        base_main_window.TaggingPage = TaggingPage
        base_main_window.YandexMapsPage = YandexMapsPage
        super().__init__(theme_manager)
