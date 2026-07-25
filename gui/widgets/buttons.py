from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QWidget

from core.paths import resource_path
from core.svg_loader import load_svg_icon


def _refresh_style(widget: QWidget) -> None:
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


class BaseButton(QPushButton):
    """Общая база для кнопок Teggy."""

    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
        *,
        variant: str = "default",
        icon_size: QSize = QSize(20, 20),
    ) -> None:
        super().__init__(text, parent)
        self._icon_size = QSize(icon_size)
        self._busy = False
        self._normal_text = text
        self.setProperty("variant", variant)
        self.setIconSize(self._icon_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_icon(self, icon: QIcon) -> None:
        self.setIcon(icon)
        self.setIconSize(self._icon_size)

    def set_icon_size(self, size: QSize) -> None:
        self._icon_size = QSize(size)
        self.setIconSize(self._icon_size)

    def icon_size(self) -> QSize:
        return QSize(self._icon_size)

    def set_variant(self, variant: str) -> None:
        if self.property("variant") == variant:
            return
        self.setProperty("variant", variant)
        _refresh_style(self)

    def variant(self) -> str:
        return str(self.property("variant") or "default")

    def set_busy(self, busy: bool, text: str = "Загрузка…") -> None:
        busy = bool(busy)
        if self._busy == busy:
            return

        self._busy = busy
        self.setProperty("busy", busy)
        if busy:
            self._normal_text = self.text()
            self.setText(text)
            self.setEnabled(False)
        else:
            self.setText(self._normal_text)
            self.setEnabled(True)
        _refresh_style(self)

    def is_busy(self) -> bool:
        return self._busy


class PrimaryButton(BaseButton):
    """Главная кнопка действия."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent, variant="primary")
        self.setProperty("class", "PrimaryButton")


class SecondaryButton(BaseButton):
    """Второстепенная кнопка."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent, variant="secondary")
        self.setProperty("class", "SecondaryButton")


class DangerButton(BaseButton):
    """Опасное или необратимое действие."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent, variant="danger")
        self.setProperty("class", "DangerButton")


class SuccessButton(BaseButton):
    """Положительное или подтверждающее действие."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent, variant="success")
        self.setProperty("class", "SuccessButton")


class IconButton(BaseButton):
    """Кнопка с SVG-иконкой."""

    def __init__(
        self,
        icon_path: str,
        tooltip: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__("", parent, variant="icon")
        self.setProperty("class", "IconButton")
        self._icon_path = icon_path
        self._color = "#FFFFFF"
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)
        self.reload_icon()

    def set_color(self, color: str) -> None:
        if self._color != color:
            self._color = color
            self.reload_icon()

    def color(self) -> str:
        return self._color

    def set_icon_path(self, icon_path: str) -> None:
        if self._icon_path != icon_path:
            self._icon_path = icon_path
            self.reload_icon()

    def reload_icon(self) -> None:
        self.setIcon(load_svg_icon(resource_path(self._icon_path), self._color))
        self.setIconSize(self._icon_size)
