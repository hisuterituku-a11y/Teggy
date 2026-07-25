from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QSizePolicy, QWidget


class Divider(QFrame):
    """Универсальный горизонтальный или вертикальный разделитель."""

    def __init__(
        self,
        orientation: str | Qt.Orientation = "horizontal",
        parent: Optional[QWidget] = None,
        *,
        thickness: int = 1,
        variant: str = "default",
    ) -> None:
        super().__init__(parent)

        self.setObjectName("divider")
        self.setProperty("class", "Divider")
        self.setProperty("variant", variant)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._orientation = self._normalize_orientation(orientation)
        self._thickness = max(1, int(thickness))
        self._apply_orientation()

    @staticmethod
    def _normalize_orientation(
        orientation: str | Qt.Orientation,
    ) -> Qt.Orientation:
        if isinstance(orientation, Qt.Orientation):
            return orientation

        value = str(orientation).strip().lower()
        if value in {"vertical", "v", "вертикальный"}:
            return Qt.Orientation.Vertical
        return Qt.Orientation.Horizontal

    def _apply_orientation(self) -> None:
        is_horizontal = self._orientation == Qt.Orientation.Horizontal
        self.setProperty("orientation", "horizontal" if is_horizontal else "vertical")

        if is_horizontal:
            self.setFrameShape(QFrame.Shape.HLine)
            self.setFixedHeight(self._thickness)
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
            self.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
        else:
            self.setFrameShape(QFrame.Shape.VLine)
            self.setFixedWidth(self._thickness)
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Expanding,
            )

    def orientation(self) -> Qt.Orientation:
        return self._orientation

    def set_orientation(self, orientation: str | Qt.Orientation) -> None:
        normalized = self._normalize_orientation(orientation)
        if normalized == self._orientation:
            return
        self._orientation = normalized
        self._apply_orientation()

    @classmethod
    def horizontal(
        cls,
        parent: Optional[QWidget] = None,
        **kwargs,
    ) -> "Divider":
        return cls(Qt.Orientation.Horizontal, parent, **kwargs)

    @classmethod
    def vertical(
        cls,
        parent: Optional[QWidget] = None,
        **kwargs,
    ) -> "Divider":
        return cls(Qt.Orientation.Vertical, parent, **kwargs)
