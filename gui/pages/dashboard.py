from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.dashboard_data import (
    get_current_task,
    get_dashboard_stats,
    get_recent_files,
)
from gui.components.cards import (
    FileList,
    HeroPanel,
    ProjectRow,
    StatsBlock,
    TaskCard,
)


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("DashboardPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("#DashboardPage { background: #070B18; }")

        stats = get_dashboard_stats()
        task = get_current_task()
        files = get_recent_files()

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(18)

        hero = QHBoxLayout()
        hero.setSpacing(18)
        hero_panel = HeroPanel()
        stats_block = StatsBlock(stats)
        stats_block.setMinimumWidth(330)
        hero.addWidget(hero_panel, 2)
        hero.addWidget(stats_block, 1)
        root.addLayout(hero)

        middle = QHBoxLayout()
        middle.setSpacing(18)
        task_card = TaskCard(task)
        file_list = FileList(files)
        file_list.setMinimumWidth(350)
        file_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._polish_recent_files(file_list)
        middle.addWidget(task_card, 2)
        middle.addWidget(file_list, 1)
        root.addLayout(middle)

        projects_title = ProjectRow("Недавние проекты", "Открыть все")
        root.addWidget(projects_title)
        root.addStretch(1)

    @staticmethod
    def _polish_recent_files(file_list: FileList) -> None:
        """Не даём строкам последних файлов схлопываться при узком окне."""
        for item in file_list.findChildren(QFrame, "FileItem"):
            item.setMinimumHeight(66)
            item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        for label in file_list.findChildren(QLabel):
            if label.objectName() in {"FileName", "FileInfo"}:
                label.setMinimumHeight(18)
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
                label.setWordWrap(False)
