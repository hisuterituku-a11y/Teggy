from __future__ import annotations

from pathlib import Path

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
    """Финальный слой страницы Wordstat с полноценными контролами."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        current = self.region_combo.currentText()
        self.region_combo.clear()
        self.region_combo.addItems(REGIONS)
        self.region_combo.setCurrentText(current if current in REGIONS else "all")
        self.region_combo.setMaxVisibleItems(18)

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
            """
        )
