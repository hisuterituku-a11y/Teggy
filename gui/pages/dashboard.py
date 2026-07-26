from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
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
    MIN_CONTENT_WIDTH = 940
    MIN_CONTENT_HEIGHT = 730

    def __init__(self):
        super().__init__()
        self.setObjectName("DashboardPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("#DashboardPage { background: #070B18; }")
        self.setMinimumSize(self.MIN_CONTENT_WIDTH, self.MIN_CONTENT_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        stats = get_dashboard_stats()
        task = get_current_task()
        files = get_recent_files()

        root = QVBoxLayout(self)
        root.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(18)

        hero = QHBoxLayout()
        hero.setSpacing(18)

        hero_panel = HeroPanel()
        hero_panel.setMinimumWidth(570)
        hero_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        stats_block = StatsBlock(stats)
        stats_block.setMinimumWidth(320)
        stats_block.setMaximumWidth(380)
        stats_block.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        hero.addWidget(hero_panel, 1)
        hero.addWidget(stats_block, 0)
        root.addLayout(hero)

        middle = QHBoxLayout()
        middle.setSpacing(18)

        task_card = TaskCard(task)
        task_card.setMinimumWidth(570)
        task_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        file_list = FileList(files)
        file_list.setMinimumWidth(320)
        file_list.setMaximumWidth(380)
        file_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self._polish_recent_files(file_list)

        middle.addWidget(task_card, 1)
        middle.addWidget(file_list, 0)
        root.addLayout(middle)

        projects_title = ProjectRow("Недавние проекты", "Открыть все")
        projects_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        root.addWidget(projects_title)

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
