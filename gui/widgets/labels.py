from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget


class BaseLabel(QLabel):
    """Базовый текстовый компонент Teggy."""

    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
        *,
        css_class: str = "BaseLabel",
        word_wrap: bool = False,
    ) -> None:
        super().__init__(text, parent)
        self.setProperty("class", css_class)
        self.setWordWrap(word_wrap)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)


class TitleLabel(BaseLabel):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent, css_class="TitleLabel", word_wrap=True)


class SubtitleLabel(BaseLabel):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent, css_class="SubtitleLabel", word_wrap=True)


class CaptionLabel(BaseLabel):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent, css_class="CaptionLabel", word_wrap=True)


class HintLabel(BaseLabel):
    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent, css_class="HintLabel", word_wrap=True)


class BadgeLabel(BaseLabel):
    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
        *,
        variant: str = "default",
    ) -> None:
        super().__init__(text, parent, css_class="BadgeLabel")
        self.setProperty("variant", variant)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class StatusLabel(BadgeLabel):
    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
        *,
        status: str = "neutral",
    ) -> None:
        super().__init__(text, parent, variant=status)
        self.setProperty("class", "StatusLabel")
        self.setProperty("status", status)


class IconLabel(BaseLabel):
    """Лейбл с текстом; путь к иконке хранится как dynamic property."""

    def __init__(
        self,
        icon_path: str,
        text: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent, css_class="IconLabel")
        self._icon_path = icon_path
        self.setProperty("iconPath", icon_path)

    def icon_path(self) -> str:
        return self._icon_path

    def set_icon_path(self, icon_path: str) -> None:
        self._icon_path = icon_path
        self.setProperty("iconPath", icon_path)
