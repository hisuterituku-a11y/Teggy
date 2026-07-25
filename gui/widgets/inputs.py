from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QLineEdit, QTextEdit, QWidget


def _refresh_style(widget: QWidget) -> None:
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


class InputStateMixin:
    """Добавляет визуальные состояния полям ввода."""

    def set_state(self, state: str = "default", message: str = "") -> None:
        self.setProperty("state", state)
        self.setProperty("stateMessage", message)
        self.setToolTip(message)
        _refresh_style(self)

    def set_error(self, message: str = "") -> None:
        self.set_state("error", message)

    def set_success(self, message: str = "") -> None:
        self.set_state("success", message)

    def set_warning(self, message: str = "") -> None:
        self.set_state("warning", message)

    def clear_state(self) -> None:
        self.set_state("default", "")


class TextField(InputStateMixin, QLineEdit):
    """Однострочное поле ввода."""

    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setProperty("class", "TextField")
        self.setProperty("state", "default")
        self.setClearButtonEnabled(True)


class SearchField(TextField):
    """Поле поиска."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        placeholder: str = "Поиск…",
    ) -> None:
        super().__init__(placeholder, parent)
        self.setProperty("class", "SearchField")


class TagEditor(InputStateMixin, QTextEdit):
    """Многострочное поле для тегов."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        placeholder: str = "Введите теги (по одному на строке)",
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "TagEditor")
        self.setProperty("state", "default")
        self.setPlaceholderText(placeholder)
        self.setAcceptRichText(False)

    def tags(self) -> list[str]:
        return [line.strip() for line in self.toPlainText().splitlines() if line.strip()]

    def set_tags(self, tags: list[str]) -> None:
        self.setPlainText("\n".join(tags))
