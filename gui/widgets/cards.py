from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


def _refresh_style(widget: QWidget) -> None:
    """Повторно применяет QSS после изменения dynamic property."""
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


class Card(QFrame):
    """Базовая карточка, совместимая со старым API."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        variant: str = "default",
        compact: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setProperty("class", "Card")
        self.setProperty("variant", variant)
        self.setProperty("compact", compact)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        margin = 12 if compact else 16
        spacing = 8 if compact else 12
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(margin, margin, margin, margin)
        self._layout.setSpacing(spacing)

    def add_widget(
        self,
        widget: QWidget,
        stretch: int = 0,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag(0),
    ) -> None:
        self._layout.addWidget(widget, stretch, alignment)

    def add_layout(self, layout: QLayout, stretch: int = 0) -> None:
        self._layout.addLayout(layout, stretch)

    def add_stretch(self, stretch: int = 1) -> None:
        self._layout.addStretch(stretch)

    def content_layout(self) -> QVBoxLayout:
        return self._layout

    def set_variant(self, variant: str) -> None:
        if self.property("variant") != variant:
            self.setProperty("variant", variant)
            _refresh_style(self)

    def variant(self) -> str:
        return str(self.property("variant") or "default")

    def set_compact(self, compact: bool) -> None:
        margin = 12 if compact else 16
        spacing = 8 if compact else 12
        self.setProperty("compact", compact)
        self._layout.setContentsMargins(margin, margin, margin, margin)
        self._layout.setSpacing(spacing)
        _refresh_style(self)


class CardHeader(QFrame):
    """Унифицированный заголовок карточки."""

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("cardHeader")
        self.setProperty("class", "CardHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)

        self._leading_layout = QHBoxLayout()
        self._leading_layout.setContentsMargins(0, 0, 0, 0)
        self._leading_layout.setSpacing(8)

        self._text_layout = QVBoxLayout()
        self._text_layout.setContentsMargins(0, 0, 0, 0)
        self._text_layout.setSpacing(2)

        self._title_label = QLabel(title, self)
        self._title_label.setObjectName("cardTitle")
        self._title_label.setProperty("class", "CardHeaderLabel")
        self._title_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self._subtitle_label = QLabel(subtitle, self)
        self._subtitle_label.setObjectName("cardSubtitle")
        self._subtitle_label.setProperty("class", "CardSubtitleLabel")
        self._subtitle_label.setWordWrap(True)
        self._subtitle_label.setVisible(bool(subtitle))

        self._text_layout.addWidget(self._title_label)
        self._text_layout.addWidget(self._subtitle_label)

        self._actions_layout = QHBoxLayout()
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(6)

        self._layout.addLayout(self._leading_layout)
        self._layout.addLayout(self._text_layout, 1)
        self._layout.addStretch()
        self._layout.addLayout(self._actions_layout)

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)

    def title(self) -> str:
        return self._title_label.text()

    def set_subtitle(self, text: str) -> None:
        self._subtitle_label.setText(text)
        self._subtitle_label.setVisible(bool(text))

    def subtitle(self) -> str:
        return self._subtitle_label.text()

    def add_left_widget(self, widget: QWidget) -> None:
        self._leading_layout.addWidget(widget)

    def add_right_widget(self, widget: QWidget) -> None:
        self._actions_layout.addWidget(widget)

    def add_action(self, widget: QWidget) -> None:
        self.add_right_widget(widget)

    def title_label(self) -> QLabel:
        return self._title_label

    def subtitle_label(self) -> QLabel:
        return self._subtitle_label


class CardBody(QFrame):
    """Тело карточки для основного содержимого."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        spacing: int = 8,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("cardBody")
        self.setProperty("class", "CardBody")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(spacing)

    def add_widget(
        self,
        widget: QWidget,
        stretch: int = 0,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag(0),
    ) -> None:
        self._layout.addWidget(widget, stretch, alignment)

    def add_layout(self, layout: QLayout, stretch: int = 0) -> None:
        self._layout.addLayout(layout, stretch)

    def add_stretch(self, stretch: int = 1) -> None:
        self._layout.addStretch(stretch)

    def content_layout(self) -> QVBoxLayout:
        return self._layout


class PremiumCard(Card):
    """Составная карточка с заголовком, телом и сворачиванием."""

    collapsed_changed = Signal(bool)

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent: Optional[QWidget] = None,
        *,
        variant: str = "default",
        collapsible: bool = False,
        collapsed: bool = False,
        compact: bool = False,
    ) -> None:
        super().__init__(parent, variant=variant, compact=compact)
        self.setObjectName("premiumCard")
        self.setProperty("premium", True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._collapsible = collapsible
        self._collapsed = False
        self.header = CardHeader(title=title, subtitle=subtitle, parent=self)
        self.body = CardBody(parent=self)

        self._collapse_button = QToolButton(self.header)
        self._collapse_button.setObjectName("cardCollapseButton")
        self._collapse_button.setProperty("class", "CardCollapseButton")
        self._collapse_button.setAutoRaise(True)
        self._collapse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._collapse_button.clicked.connect(self.toggle_collapsed)
        self._collapse_button.setVisible(collapsible)
        self.header.add_right_widget(self._collapse_button)

        super().add_widget(self.header)
        super().add_widget(self.body)
        self.header.setVisible(bool(title or subtitle or collapsible))

        if collapsed:
            self.set_collapsed(True)
        else:
            self._update_collapse_button()

    def add_widget(
        self,
        widget: QWidget,
        stretch: int = 0,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag(0),
    ) -> None:
        self.body.add_widget(widget, stretch, alignment)

    def add_layout(self, layout: QLayout, stretch: int = 0) -> None:
        self.body.add_layout(layout, stretch)

    def add_stretch(self, stretch: int = 1) -> None:
        self.body.add_stretch(stretch)

    def content_layout(self) -> QVBoxLayout:
        return self.body.content_layout()

    def set_title(self, text: str) -> None:
        self.header.set_title(text)
        self._sync_header_visibility()

    def set_subtitle(self, text: str) -> None:
        self.header.set_subtitle(text)
        self._sync_header_visibility()

    def add_header_widget(self, widget: QWidget) -> None:
        self.header.add_left_widget(widget)
        self.header.show()

    def add_action(self, widget: QWidget) -> None:
        self.header.add_action(widget)
        self.header.show()

    def set_collapsible(self, collapsible: bool) -> None:
        self._collapsible = collapsible
        self._collapse_button.setVisible(collapsible)
        if not collapsible and self._collapsed:
            self.set_collapsed(False)
        self._sync_header_visibility()

    def is_collapsible(self) -> bool:
        return self._collapsible

    def set_collapsed(self, collapsed: bool) -> None:
        collapsed = bool(collapsed)
        if collapsed and not self._collapsible:
            return
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed
        self.body.setVisible(not collapsed)
        self.setProperty("collapsed", collapsed)
        self._update_collapse_button()
        _refresh_style(self)
        self.collapsed_changed.emit(collapsed)

    def is_collapsed(self) -> bool:
        return self._collapsed

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)

    def _update_collapse_button(self) -> None:
        if self._collapsed:
            self._collapse_button.setArrowType(Qt.ArrowType.RightArrow)
            self._collapse_button.setToolTip("Развернуть карточку")
        else:
            self._collapse_button.setArrowType(Qt.ArrowType.DownArrow)
            self._collapse_button.setToolTip("Свернуть карточку")

    def _sync_header_visibility(self) -> None:
        has_text = bool(self.header.title() or self.header.subtitle())
        self.header.setVisible(has_text or self._collapsible)
