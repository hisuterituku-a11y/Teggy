# ============================================================
# Teggy TopBar
# Sprint 3.8
#
# Верхняя панель приложения.
#
# Здесь находятся:
# - название страницы
# - поиск
# - быстрые действия
#
# Важно:
# objectName используются в QSS.
# Не переименовывать без обновления темы.
# ============================================================


from pathlib import Path
from PySide6.QtCore import QSize

from PySide6.QtGui import QIcon

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

# ============================================================
# Sprint 3.9 Icon loader
#
# Единая точка загрузки SVG.
#
# Пока используется только TopBar.
# Позже вынесем в gui/utils/icons.py
# ============================================================


ICON_PATH = (
    Path(__file__)
    .resolve()
    .parents[2]
    / "assets"
    / "icons"
    / "teggy"
)


def load_icon(name):
    return QIcon(
        str(
            ICON_PATH / f"{name}.svg"
        )
    )


class TopBar(QFrame):

    def __init__(self):

        super().__init__()

        self.setObjectName(
            "TopBar"
        )


        layout = QHBoxLayout(self)


        # Общие отступы topbar.
        # Не увеличивать без проверки Dashboard.
        layout.setContentsMargins(
            24,
            12,
            24,
            12
        )


        layout.setSpacing(
            10
        )


        # =========================
        # PAGE TITLE
        # =========================

        title = QLabel(
            "Главная"
        )

        title.setObjectName(
            "PageTitle"
        )


        layout.addWidget(
            title
        )


        layout.addStretch()



        # =========================
        # SEARCH
        # =========================

        search = QLineEdit()

        search.setObjectName(
            "Search"
        )

        search.setPlaceholderText(
            "Поиск..."
        )


        # фиксируем комфортный размер,
        # чтобы поиск не съедал панель

        search.setMinimumWidth(
            360
        )

        search.setMaximumWidth(
            520
        )


        layout.addWidget(
            search
        )



        # =========================
        # THEME BUTTON
        # =========================

        theme_button = QPushButton()

        theme_button.setIcon(
            load_icon("sun")
        )

        theme_button.setIconSize(
            QSize(22, 22)
        )

        theme_button.setObjectName(
            "ThemeButton"
        )


        layout.addWidget(
            theme_button
        )



        # =========================
        # NOTIFICATIONS
        # =========================

        notify_button = QPushButton()

        notify_button.setIcon(
            load_icon("bell")
        )

        notify_button.setIconSize(
            QSize(22, 22)
        )

        notify_button.setObjectName(
            "NotifyButton"
        )


        layout.addWidget(
            notify_button
        )



        # =========================
        # PROFILE
        # =========================

        profile_button = QPushButton(
            "LU"
        )

        profile_button.setObjectName(
            "ProfileButton"
        )


        layout.addWidget(
            profile_button
        )