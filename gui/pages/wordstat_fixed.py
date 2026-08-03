from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCompleter

from gui.pages.wordstat import WordstatPage as BaseWordstatPage


REGIONS = [
    "all",
    "Москва",
    "Санкт-Петербург",
    "Астрахань",
    "Барнаул",
    "Белгород",
    "Брянск",
    "Владивосток",
    "Владимир",
    "Волгоград",
    "Воронеж",
    "Екатеринбург",
    "Иваново",
    "Ижевск",
    "Иркутск",
    "Казань",
    "Калининград",
    "Калуга",
    "Кемерово",
    "Киров",
    "Краснодар",
    "Красноярск",
    "Курск",
    "Липецк",
    "Махачкала",
    "Набережные Челны",
    "Нижний Новгород",
    "Новокузнецк",
    "Новосибирск",
    "Омск",
    "Оренбург",
    "Пенза",
    "Пермь",
    "Петрозаводск",
    "Ростов-на-Дону",
    "Рязань",
    "Самара",
    "Саранск",
    "Саратов",
    "Севастополь",
    "Симферополь",
    "Смоленск",
    "Сочи",
    "Ставрополь",
    "Сургут",
    "Тверь",
    "Тольятти",
    "Томск",
    "Тула",
    "Тюмень",
    "Улан-Удэ",
    "Ульяновск",
    "Уфа",
    "Хабаровск",
    "Чебоксары",
    "Челябинск",
    "Ярославль",
]


class WordstatPage(BaseWordstatPage):
    """Финальный слой страницы Wordstat с поиском региона по вводу."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.region_combo.clear()
        self.region_combo.addItems(REGIONS)
        self.region_combo.setEditable(True)
        self.region_combo.setInsertPolicy(self.region_combo.InsertPolicy.NoInsert)
        self.region_combo.setCurrentText("all")
        self.region_combo.setMaxVisibleItems(12)

        completer = QCompleter(REGIONS, self.region_combo)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setMaxVisibleItems(12)
        self.region_combo.setCompleter(completer)
        self._region_completer = completer

        popup = completer.popup()
        popup.setObjectName("WordstatRegionPopup")
        popup.setUniformItemSizes(True)
        popup.setStyleSheet(
            """
            QListView#WordstatRegionPopup {
                color: #eef2ff;
                background: #121a2f;
                border: 1px solid #33415f;
                border-radius: 10px;
                padding: 6px;
                outline: none;
                selection-background-color: #6d3fc0;
                selection-color: #ffffff;
            }
            QListView#WordstatRegionPopup::item {
                min-height: 30px;
                padding: 4px 10px;
                border-radius: 6px;
            }
            QListView#WordstatRegionPopup::item:hover {
                background: #21304f;
                color: #ffffff;
            }
            QListView#WordstatRegionPopup::item:selected {
                background: #6d3fc0;
                color: #ffffff;
            }
            QScrollBar:vertical {
                width: 10px;
                margin: 4px 2px 4px 2px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                min-height: 28px;
                border-radius: 5px;
                background: #465675;
            }
            QScrollBar::handle:vertical:hover {
                background: #6d4bc3;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                width: 0;
                height: 0;
                background: transparent;
            }
            """
        )

        line_edit = self.region_combo.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText("Начните вводить город")
            line_edit.setClearButtonEnabled(True)

        self.region_combo.setToolTip(
            "Начните вводить город и выберите подходящий вариант. "
            "Для поиска без ограничения по региону оставьте all."
        )

        icon_dir = Path(__file__).resolve().parents[2] / "assets" / "icons" / "teggy"
        down = (icon_dir / "chevron-down.svg").as_posix()
        up = (icon_dir / "chevron-up.svg").as_posix()

        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QComboBox#WordstatCombo::down-arrow {{
                image: url(\"{down}\");
                width: 14px;
                height: 14px;
            }}
            QSpinBox#WordstatSpin::up-arrow {{
                image: url(\"{up}\");
                width: 12px;
                height: 12px;
            }}
            QSpinBox#WordstatSpin::down-arrow {{
                image: url(\"{down}\");
                width: 12px;
                height: 12px;
            }}
            QComboBox#WordstatCombo QLineEdit {{
                color: #eef2ff;
                background: transparent;
                border: none;
                padding: 0;
                selection-background-color: #7c3aed;
            }}
            """
        )
