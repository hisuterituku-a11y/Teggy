from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Toolbar(QFrame):
    """Верхняя панель страницы с заголовком, подзаголовком и действиями."""

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent: Optional[QWidget] = None,
        *,
        compact: bool = False,
        variant: str = "default",
    ) -> None:
        super().__init__(parent)

        self.setObjectName("toolbar")
        self.setProperty("class", "Toolbar")
        self.setProperty("variant", variant)
        self.setProperty("compact", compact)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        margins = (0, 0, 0, 0) if compact else (0, 0, 0, 8)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(*margins)
        self._layout.setSpacing(12)

        self._leading_layout = QHBoxLayout()
        self._leading_layout.setContentsMargins(0, 0, 0, 0)
        self._leading_layout.setSpacing(8)

        self._text_layout = QVBoxLayout()
        self._text_layout.setContentsMargins(0, 0, 0, 0)
        self._text_layout.setSpacing(3)

        self._title_label = QLabel(title, self)
        self._title_label.setObjectName("toolbarTitle")
        self._title_label.setProperty("class", "ToolbarTitle")
        self._title_label.setWordWrap(True)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self._subtitle_label = QLabel(subtitle, self)
        self._subtitle_label.setObjectName("toolbarSubtitle")
        self._subtitle_label.setProperty("class", "ToolbarSubtitle")
        self._subtitle_label.setWordWrap(True)
        self._subtitle_label.setVisible(bool(subtitle))
        self._subtitle_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self._text_layout.addWidget(self._title_label)
        self._text_layout.addWidget(self._subtitle_label)

        self._actions_layout = QHBoxLayout()
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(8)

        self._layout.addLayout(self._leading_layout)
        self._layout.addLayout(self._text_layout, 1)
        self._layout.addStretch()
        self._layout.addLayout(self._actions_layout)

        self._sync_text_visibility()

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)
        self._sync_text_visibility()

    def title(self) -> str:
        return self._title_label.text()

    def set_subtitle(self, text: str) -> None:
        self._subtitle_label.setText(text)
        self._subtitle_label.setVisible(bool(text))
        self._sync_text_visibility()

    def subtitle(self) -> str:
        return self._subtitle_label.text()

    def title_label(self) -> QLabel:
        return self._title_label

    def subtitle_label(self) -> QLabel:
        return self._subtitle_label

    def add_leading_widget(self, widget: QWidget) -> None:
        self._leading_layout.addWidget(widget)

    def add_action(self, widget: QWidget) -> None:
        self._actions_layout.addWidget(widget)

    def add_actions(self, *widgets: QWidget) -> None:
        for widget in widgets:
            self.add_action(widget)

    def add_action_stretch(self, stretch: int = 1) -> None:
        self._actions_layout.addStretch(stretch)

    def actions_layout(self) -> QHBoxLayout:
        return self._actions_layout

    def _sync_text_visibility(self) -> None:
        self._title_label.setVisible(bool(self.title()))
        self._subtitle_label.setVisible(bool(self.subtitle()))
