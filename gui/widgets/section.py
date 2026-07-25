from __future__ import annotations

from typing import Optional

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

from .divider import Divider


class Section(QFrame):
    """Логическая секция страницы с заголовком, действиями и содержимым."""

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent: Optional[QWidget] = None,
        *,
        show_divider: bool = True,
        spacing: int = 12,
        content_spacing: int = 10,
        variant: str = "default",
    ) -> None:
        super().__init__(parent)

        self.setObjectName("section")
        self.setProperty("class", "Section")
        self.setProperty("variant", variant)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(spacing)

        self.header = QFrame(self)
        self.header.setObjectName("sectionHeader")
        self.header.setProperty("class", "SectionHeader")
        self.header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._header_layout = QHBoxLayout(self.header)
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout.setSpacing(10)

        self._text_layout = QVBoxLayout()
        self._text_layout.setContentsMargins(0, 0, 0, 0)
        self._text_layout.setSpacing(2)

        self._title_label = QLabel(title, self.header)
        self._title_label.setObjectName("sectionTitle")
        self._title_label.setProperty("class", "SectionTitle")
        self._title_label.setWordWrap(True)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self._subtitle_label = QLabel(subtitle, self.header)
        self._subtitle_label.setObjectName("sectionSubtitle")
        self._subtitle_label.setProperty("class", "SectionSubtitle")
        self._subtitle_label.setWordWrap(True)
        self._subtitle_label.setVisible(bool(subtitle))
        self._subtitle_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self._text_layout.addWidget(self._title_label)
        self._text_layout.addWidget(self._subtitle_label)

        self._actions_layout = QHBoxLayout()
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(6)

        self._header_layout.addLayout(self._text_layout, 1)
        self._header_layout.addStretch()
        self._header_layout.addLayout(self._actions_layout)

        self.divider = Divider.horizontal(self)
        self.divider.setProperty("class", "SectionDivider")
        self.divider.setVisible(show_divider)

        self.body = QFrame(self)
        self.body.setObjectName("sectionBody")
        self.body.setProperty("class", "SectionBody")
        self.body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._content_layout = QVBoxLayout(self.body)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(content_spacing)

        self._root_layout.addWidget(self.header)
        self._root_layout.addWidget(self.divider)
        self._root_layout.addWidget(self.body)

        self._sync_header_visibility()

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)
        self._sync_header_visibility()

    def title(self) -> str:
        return self._title_label.text()

    def set_subtitle(self, text: str) -> None:
        self._subtitle_label.setText(text)
        self._subtitle_label.setVisible(bool(text))
        self._sync_header_visibility()

    def subtitle(self) -> str:
        return self._subtitle_label.text()

    def title_label(self) -> QLabel:
        return self._title_label

    def subtitle_label(self) -> QLabel:
        return self._subtitle_label

    def add_action(self, widget: QWidget) -> None:
        self._actions_layout.addWidget(widget)
        self.header.show()

    def add_widget(
        self,
        widget: QWidget,
        stretch: int = 0,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag(0),
    ) -> None:
        self._content_layout.addWidget(widget, stretch, alignment)

    def add_layout(self, layout: QLayout, stretch: int = 0) -> None:
        self._content_layout.addLayout(layout, stretch)

    def add_stretch(self, stretch: int = 1) -> None:
        self._content_layout.addStretch(stretch)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def set_divider_visible(self, visible: bool) -> None:
        self.divider.setVisible(bool(visible))

    def _sync_header_visibility(self) -> None:
        has_text = bool(self.title() or self.subtitle())
        self.header.setVisible(has_text)
        self.divider.setVisible(self.divider.isVisible() and has_text)
