# ============================================================
# Teggy Dashboard Cards
# Sprint 3.6
#
# Улучшение главного экрана:
# - более "premium" карточки
# - статистика с donut chart
# - подготовка под реальные данные
#
# Важно:
# Имена основных классов не менять.
# Dashboard зависит от них.
# ============================================================
from PySide6.QtGui import QPixmap

from PySide6.QtCore import (
    Qt,
    Signal,
    QRectF,
)

from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
)

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QProgressBar,
)
from pathlib import Path


# ============================================================
# BaseCard
#
# Общий контейнер карточек Dashboard.
#
# Здесь только поведение.
# Внешний вид -> style.qss
# ============================================================

class BaseCard(QFrame):

    def __init__(
        self,
        object_name="Card"
    ):
        super().__init__()

        self.setObjectName(
            object_name
        )

        self.setAttribute(
            Qt.WA_StyledBackground,
            True
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )



# ============================================================
# HeroPanel
#
# Главный CTA-блок.
#
# Содержит быстрые действия:
# - папка
# - AI теги
# - Яндекс
# ============================================================

class HeroPanel(BaseCard):

    def __init__(self):

        super().__init__(
            "HeroPanel"
        )

        self.setMinimumHeight(
            300
        )


        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            28,
            24,
            28,
            24
        )

        layout.setSpacing(
            12
        )


        title = QLabel(
            "Быстрый старт"
        )

        title.setObjectName(
            "HeroTitle"
        )


        subtitle = QLabel(
            "Выберите действие для начала работы"
        )

        subtitle.setObjectName(
            "HeroSubtitle"
        )


        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )


        actions = QHBoxLayout()

        actions.setSpacing(
            14
        )


        actions.addWidget(
            QuickStartCard(
                "folder",
                "Выбрать папку",
                "Загрузить фото для обработки"
            )
        )


        actions.addWidget(
            QuickStartCard(
                "tag",
                "Создать теги",
                "AI создаст SEO-теги"
            )
        )


        actions.addWidget(
            QuickStartCard(
                "cloud",
                "Выгрузить в Яндекс",
                "Опубликовать данные"
            )
        )


        layout.addLayout(
            actions
        )



# ============================================================
# QuickStartCard
#
# Карточка быстрого действия.
# ============================================================

class QuickStartCard(BaseCard):

    clicked = Signal()


    def __init__(
        self,
        icon,
        title,
        description
    ):

        super().__init__(
            "QuickStartCard"
        )


        self.setFixedHeight(
            150
        )


        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            18,
            16,
            18,
            16
        )


        layout.setSpacing(
            6
        )


        icon_label = QLabel()

        icon_label.setObjectName(
            "CardIcon"
        )

        icon_label.setPixmap(
            QPixmap(
                f"assets/icons/teggy/{icon}.svg"
            ).scaled(
                32,
                32,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )


        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "CardTitle"
        )


        desc_label = QLabel(
            description
        )

        desc_label.setObjectName(
            "CardSubtitle"
        )


        layout.addWidget(
            icon_label
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            desc_label
        )


        layout.addStretch()



        button = QPushButton(
            "→"
        )

        button.setObjectName(
            "RoundButton"
        )


        button.clicked.connect(
            self.clicked.emit
        )


        row = QHBoxLayout()

        row.addStretch()

        row.addWidget(
            button
        )


        layout.addLayout(
            row
        )



# ============================================================
# StatsDonut
#
# Круговая диаграмма статистики.
#
# Пока данные локальные.
# Позже сюда подключим реальные значения.
# ============================================================

class StatsDonut(QFrame):

    def __init__(
        self
    ):
        super().__init__()


        self.setFixedSize(
            120,
            120
        )


        self.values = [
            55,
            25,
            20
        ]


    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )


        rect = QRectF(
            10,
            10,
            100,
            100
        )


        pen = QPen()

        pen.setWidth(
            12
        )


        start = 0


        colors = [
            "#915CFF",
            "#21D99A",
            "#FFB547",
        ]


        for value, color in zip(
            self.values,
            colors
        ):

            pen.setColor(
                color
            )

            painter.setPen(
                pen
            )


            span = (
                value / 100
            ) * 360 * 16


            painter.drawArc(
                rect,
                start,
                int(span)
            )


            start += int(span)



        painter.setPen(
            Qt.NoPen
        )


        painter.setBrush(
            QBrush("#0E1428")
        )


        painter.drawEllipse(
            QRectF(
                35,
                35,
                50,
                50
            )
        )


        painter.end()

# ============================================================
# StatsBlock
#
# Правая верхняя карточка статистики.
#
# Sprint 3.6:
# Добавлена donut-диаграмма.
# ============================================================
class StatsBlock(BaseCard):

    def __init__(
        self,
        stats=None
    ):

        super().__init__(
            "StatsBlock"
        )


        if stats is None:

            stats = {
                "total": 2847,
                "photos": 1245,
                "stories": 892,
                "reviews": 456,
                "processed": 127,
                "saved_time": "12 ч 45 мин"
            }


        self.setMinimumWidth(
            320
        )


        layout = QVBoxLayout(self)


        layout.setContentsMargins(
            22,
            22,
            22,
            22
        )


        title = QLabel(
            "Статистика"
        )

        title.setObjectName(
            "SectionTitle"
        )


        layout.addWidget(
            title
        )


        chart_row = QHBoxLayout()


        donut = StatsDonut()


        chart_row.addWidget(
            donut
        )


        total_box = QVBoxLayout()


        total = QLabel(
            str(stats["total"])
        )

        total.setObjectName(
            "StatValue"
        )


        total_text = QLabel(
            "Всего файлов"
        )

        total_text.setObjectName(
            "StatTitle"
        )


        total_box.addWidget(
            total
        )


        total_box.addWidget(
            total_text
        )


        chart_row.addLayout(
            total_box
        )


        layout.addLayout(
            chart_row
        )



        stats_rows = [
            (
                stats["photos"],
                "Фото"
            ),
            (
                stats["stories"],
                "Сторис"
            ),
            (
                stats["reviews"],
                "Отзывы"
            ),
        ]


        for value, name in stats_rows:


            row = QHBoxLayout()


            label = QLabel(
                name
            )

            label.setObjectName(
                "StatTitle"
            )


            number = QLabel(
                str(value)
            )

            number.setObjectName(
                "StatValueSmall"
            )


            row.addWidget(
                label
            )


            row.addStretch()


            row.addWidget(
                number
            )


            layout.addLayout(
                row
            )



        layout.addSpacing(
            10
        )


        footer = QLabel(
            f"Сегодня обработано: {stats['processed']} файлов\n"
            f"Сэкономлено времени: {stats['saved_time']}"
        )

        footer.setObjectName(
            "StatsFooter"
        )


        layout.addWidget(
            footer
        )



# ============================================================
# TaskCard
#
# Текущая задача обработки.
#
# ============================================================

class TaskCard(BaseCard):

    def __init__(
        self,
        task=None
    ):

        super().__init__(
            "TaskCard"
        )


        if task is None:

            task = {
                "name": "Кофейня «Вкусно»",
                "current": 67,
                "total": 120,
                "progress": 56,
                "status": "🟢 В процессе"
            }


        self.setMinimumHeight(
            260
        )


        layout = QVBoxLayout(
            self
        )


        header = QHBoxLayout()


        title = QLabel(
            "Текущая задача"
        )

        title.setObjectName(
            "SectionTitle"
        )


        status = QLabel(
        task["status"]
        )

        status.setObjectName(
            "TaskStatus"
        )


        header.addWidget(
            title
        )


        header.addStretch()


        header.addWidget(
            status
        )


        layout.addLayout(
            header
        )



        info_layout = QHBoxLayout()


        image_icon = QLabel()

        image_icon.setPixmap(
            QPixmap(
                "assets/icons/teggy/photo.svg"
            ).scaled(
                18,
                18,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )


        info = QLabel(
            f"{task['name']}\n\n"
            "Обработка фото из папки\n"
            f"Обрабатываем: {task['current']} из {task['total']}"
        )


        info.setObjectName(
            "TaskText"
        )


        info_layout.addWidget(
            image_icon
        )


        info_layout.addWidget(
            info
        )


        layout.addLayout(
            info_layout
        )



        progress = QProgressBar()


        progress.setObjectName(
            "TaskProgress"
        )


        progress.setValue(
            task["progress"]
        )


        progress.setFormat(
            "56%"
        )


        layout.addWidget(
            progress
        )



        bottom = QLabel(
            "✨ AI генерирует теги\n"
            "⏱ Осталось примерно 00:01:02"
        )


        bottom.setObjectName(
            "TaskFooter"
        )


        layout.addWidget(
            bottom
        )



# ============================================================
# FileItem
#
# Одна строка файла.
#
# Отдельный класс нужен,
# чтобы потом добавить:
# - превью
# - размер
# - дату
# ============================================================

class FileItem(QFrame):

    def __init__(
        self,
        filename,
        info
    ):

        super().__init__()


        self.setObjectName(
            "FileItem"
        )


        layout = QHBoxLayout(
            self
        )


        layout.setContentsMargins(
            8,
            6,
            8,
            6
        )


        icon = QLabel()

        icon.setPixmap(
            QPixmap(
                "assets/icons/teggy/photo.svg"
            ).scaled(
                18,
                18,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )


        text_box = QVBoxLayout()


        name = QLabel(
            filename
        )

        name.setObjectName(
            "FileName"
        )


        details = QLabel(
            info
        )

        details.setObjectName(
            "FileInfo"
        )


        text_box.addWidget(
            name
        )


        text_box.addWidget(
            details
        )


        layout.addWidget(
            icon
        )


        layout.addLayout(
            text_box
        )


        layout.addStretch()



# ============================================================
# FileList
#
# Последние файлы.
#
# ============================================================

class FileList(BaseCard):

    def __init__(
        self,
        files=None
    ):

        super().__init__(
            "FileList"
        )


        if files is None:

            files = [
                (
                    "coffee_shop_01.jpg",
                    "Фото • 2.4 MB • 12:45"
                ),
                (
                    "story_2024_01.mp4",
                    "Сторис • 15.8 MB • 12:43"
                ),
                (
                    "review_155_01.jpg",
                    "Отзыв • 1.1 MB • 12:40"
                ),
            ]


        layout = QVBoxLayout(
            self
        )


        title = QLabel(
            "Последние файлы"
        )


        title.setObjectName(
            "SectionTitle"
        )


        layout.addWidget(
            title
        )


        for filename, info in files:

            layout.addWidget(
                FileItem(
                    filename,
                    info
                )
            )



# ============================================================
# ProjectRow
#
# Нижний блок проекта.
#
# ============================================================

class ProjectRow(BaseCard):

    def __init__(
        self,
        name,
        info
    ):

        super().__init__(
            "ProjectRow"
        )


        self.setFixedHeight(
            70
        )


        layout = QHBoxLayout(
            self
        )


        row = QHBoxLayout()


        folder_icon = QLabel()

        folder_icon.setPixmap(
            QPixmap(
                "assets/icons/teggy/folder.svg"
            ).scaled(
                18,
                18,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )


        title = QLabel(
            name
        )

        title.setObjectName(
            "ProjectTitle"
        )


        row.addWidget(
            folder_icon
        )

        row.addWidget(
            title
        )

        row.addStretch()

        title.setObjectName(
            "ProjectTitle"
        )


        subtitle = QLabel(
            info
        )

        subtitle.setObjectName(
            "ProjectInfo"
        )


        layout.addWidget(
            title
        )


        layout.addStretch()


        layout.addWidget(
            subtitle
        )
        