# ============================================================
# Teggy Sidebar
# Sprint 3.7
#
# Левая панель приложения.
#
# Добавлено:
# - брендовый блок
# - версия приложения
# - активный пункт меню
# - PRO карточка
# - профиль пользователя
#
# Важно:
# objectName используются в style.qss.
# Не переименовывать без обновления темы.
# ============================================================


from pathlib import Path
from PySide6.QtCore import QSize, Qt

from PySide6.QtGui import QIcon, QPixmap

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

# ============================================================
# Sprint 3.10 Icon loader
#
# Загрузка SVG для Sidebar.
#
# Пока локально.
# Позже можно вынести в общий icon helper.
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


class Sidebar(QFrame):

    def __init__(self):

        super().__init__()


        self.setObjectName(
            "Sidebar"
        )


        self.setFixedWidth(
            252
        )


        layout = QVBoxLayout(
            self
        )


        layout.setContentsMargins(
            18,
            24,
            18,
            20
        )


        layout.setSpacing(
            8
        )


        # ====================================================
        # BRAND
        #
        # Логотип и версия приложения.
        # ====================================================


        # ====================================================
        # BRAND ICON
        #
        # Логотип Teggy SVG.
        #
        # Sprint 4.1:
        # - фирменный pin
        # - прозрачный фон
        # - готовность под темы
        # ====================================================


        brand = QHBoxLayout()

        brand.setSpacing(
            6
        )

        brand.setAlignment(
            Qt.AlignLeft
        )

        brand_icon = QLabel()

        brand_icon.setObjectName(
            "LogoIcon"
        )


        pixmap = QPixmap(
            str(
                ICON_PATH / "logo.png"
            )
        )


        brand_icon.setPixmap(
            pixmap.scaled(
                50,
                50,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )


        brand.addWidget(
            brand_icon
        )



        logo = QLabel(
            "Teggy"
        )

        logo.setObjectName(
            "Logo"
        )


        brand.addWidget(
            logo
        )


        brand.addStretch()


        layout.addLayout(
            brand
        )


        sub = QLabel(
            "AI PHOTO TAGGER"
        )

        sub.setObjectName(
            "LogoSub"
        )


        layout.addWidget(
            sub
        )


        version = QLabel(
            "v1.0.0"
        )

        version.setObjectName(
            "VersionLabel"
        )


        layout.addWidget(
            version
        )



        layout.addSpacing(
            28
        )



        # ====================================================
        # NAVIGATION
        #
        # Позже подключим реальные страницы.
        # ====================================================


        menu = [
            ("Главная", "home", True),
            ("Фото", "photo", False),
            ("Теги", "tag", False),
            ("Шаблоны", "templates", False),
            ("Настройки", "settings", False),
        ]


        for text, icon, active in menu:

            button = QPushButton(
                text
            )


            button.setIcon(
                load_icon(icon)
            )


            button.setIconSize(
                QSize(22, 22)
            )


            button.setObjectName(
                "SideButton"
            )


            button.setCheckable(
                True
            )
            button.page_name = text

            button.setChecked(
                active
            )


            layout.addWidget(
                button
            )



        layout.addStretch()



        # ====================================================
        # PREMIUM CARD
        #
        # Блок подписки.
        # ====================================================


        # ====================================================
        # PREMIUM CARD
        #
        # Карточка подписки.
        #
        # Sprint 3.12:
        # - убран эмодзи
        # - отдельные элементы для QSS
        # - подготовлено под реальные данные тарифа
        # ====================================================


        premium_card = QFrame()

        premium_card.setObjectName(
            "PremiumCard"
        )


        premium_layout = QVBoxLayout(
            premium_card
        )


        premium_layout.setContentsMargins(
            14,
            10,
            14,
            10
        )


        premium_layout.setSpacing(
            6
        )



        premium_title = QLabel(
            "✦ Teggy PRO"
        )

        premium_title.setObjectName(
            "PremiumTitle"
        )


        premium_layout.addWidget(
            premium_title
        )



        premium_text = QLabel(
            "Все функции открыты\n"
            "AI + Яндекс + шаблоны"
        )

        premium_text.setObjectName(
            "PremiumText"
        )


        premium_layout.addWidget(
            premium_text
        )



        layout.addWidget(
            premium_card
        )


        # ====================================================
        # USER PROFILE CARD
        #
        # Новый блок профиля.
        #
        # Отдельные элементы нужны для:
        # - красивого QSS
        # - будущих данных из Settings
        # - аватара из файла
        # ====================================================


        user_card = QFrame()

        user_card.setObjectName(
            "UserCard"
        )


        user_layout = QVBoxLayout(
            user_card
        )


        user_layout.setContentsMargins(
            14,
            12,
            14,
            12
        )


        user_layout.setSpacing(
            6
        )



        top = QHBoxLayout()


        avatar = QLabel(
            "LU"
        )


        avatar.setObjectName(
            "Avatar"
        )

        avatar.setAlignment(
            Qt.AlignCenter
        )


        top.addWidget(
            avatar
        )



        info = QVBoxLayout()


        name = QLabel(
            "Lulu"
        )

        name.setObjectName(
            "UserName"
        )


        plan = QLabel(
            "Premium"
        )

        plan.setObjectName(
            "UserPlan"
        )


        info.addWidget(
            name
        )


        info.addWidget(
            plan
        )


        top.addLayout(
            info
        )


        top.addStretch()


        user_layout.addLayout(
            top
        )



        storage = QLabel(
            "128 GB / 512 GB"
        )


        storage.setObjectName(
            "UserStorage"
        )


        user_layout.addWidget(
            storage
        )



        layout.addWidget(
            user_card
        )


