from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

from gui.components.cards import (
    HeroPanel,
    StatsBlock,
    TaskCard,
    FileList,
    ProjectRow,
)
from core.dashboard_data import (
    get_dashboard_stats,
    get_current_task,
    get_recent_files,
)


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()
        stats = get_dashboard_stats()

        task = get_current_task()

        files = get_recent_files()

        root = QVBoxLayout(self)

        root.setContentsMargins(
            32,
            24,
            32,
            24
        )

        root.setSpacing(18)


        hero = QHBoxLayout()

        hero.addWidget(
            HeroPanel(),
            2
        )

        hero.addWidget(
            StatsBlock(
                stats
            ),
            1
        )


        root.addLayout(hero)


        middle = QHBoxLayout()


        middle.addWidget(
            TaskCard(
                task
            ),
            2
        )


        middle.addWidget(
            FileList(
                files
            ),
            1
        )


        root.addLayout(
            middle
        )


        projects_title = ProjectRow(
            "Недавние проекты",
            "Открыть все"
        )

        root.addWidget(
            projects_title
        )


        root.addStretch()