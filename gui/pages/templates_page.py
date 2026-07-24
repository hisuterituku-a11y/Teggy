from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import TemplateError
from core.paths import resource_path
from core.template_manager import TemplateManager
from gui.widgets.buttons import PrimaryButton, SecondaryButton
from gui.widgets.cards import Card, CardBody, CardHeader
from gui.widgets.inputs import TagEditor, TextField


class TemplatesPage(QWidget):
    """Рабочая область управления шаблонами метаданных."""

    log_message = Signal(str)
    template_context_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "TemplatesPage TemplatesWorkspace")

        self.current_template: str | None = None
        self._loading_editor = False
        self._dirty = False
        self._template_cache: dict[str, dict] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addWidget(self._build_header())

        self.workspace = QSplitter(Qt.Horizontal)
        self.workspace.setProperty("class", "TemplatesSplitter")
        self.workspace.setChildrenCollapsible(False)
        self.workspace.addWidget(self._build_library_panel())
        self.workspace.addWidget(self._build_editor_panel())
        self.workspace.setStretchFactor(0, 1)
        self.workspace.setStretchFactor(1, 2)
        self.workspace.setSizes([340, 720])
        root.addWidget(self.workspace, stretch=1)

        root.addWidget(self._build_status_bar())

        self._connect_editor_signals()
        self._refresh_list()
        self._create_template(log_event=False)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setProperty("class", "TemplatesWorkspaceHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        title = QLabel("Templates 2.0")
        title.setProperty("class", "PageTitle")
        text_box.addWidget(title)

        subtitle = QLabel("Создавайте, находите и редактируйте наборы метаданных")
        subtitle.setProperty("class", "PageSubtitle")
        text_box.addWidget(subtitle)

        layout.addLayout(text_box)
        layout.addStretch()

        self.header_create_btn = PrimaryButton("Новый шаблон")
        self.header_create_btn.clicked.connect(self._create_template)
        layout.addWidget(self.header_create_btn)
        return header

    def _build_library_panel(self) -> QWidget:
        panel = QWidget()
        panel.setProperty("class", "TemplateLibraryPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        card = Card()
        header = CardHeader()
        header.set_title("Библиотека шаблонов")
        card.add_widget(header)

        body = CardBody()

        self.search_field = QLineEdit()
        self.search_field.setProperty("class", "TemplateSearch")
        self.search_field.setPlaceholderText("Поиск по названию и содержимому...")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.textChanged.connect(self._apply_filter)
        body.add_widget(self.search_field)

        self.library_summary = QLabel("0 шаблонов")
        self.library_summary.setProperty("class", "TemplateLibrarySummary")
        body.add_widget(self.library_summary)

        self.template_list = QListWidget()
        self.template_list.setProperty("class", "TemplateList TemplateLibrary")
        self.template_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.template_list.setAlternatingRowColors(True)
        self.template_list.itemSelectionChanged.connect(self._on_list_selection_changed)
        body.add_widget(self.template_list)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.create_btn = SecondaryButton("Создать")
        self.create_btn.clicked.connect(self._create_template)
        actions.addWidget(self.create_btn)

        self.duplicate_btn = SecondaryButton("Дублировать")
        self.duplicate_btn.clicked.connect(self._duplicate_template)
        actions.addWidget(self.duplicate_btn)

        self.delete_btn = SecondaryButton("Удалить")
        self.delete_btn.clicked.connect(self._delete_template)
        actions.addWidget(self.delete_btn)

        body.add_layout(actions)
        card.add_widget(body)
        layout.addWidget(card)
        return panel

    def _build_editor_panel(self) -> QWidget:
        panel = QWidget()
        panel.setProperty("class", "TemplateEditorPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        editor_card = Card()
        editor_header = CardHeader()
        editor_header.set_title("Редактор шаблона")
        editor_card.add_widget(editor_header)

        body = CardBody()

        self.editor_hint = QLabel("Новый шаблон")
        self.editor_hint.setProperty("class", "TemplateEditorHint")
        body.add_widget(self.editor_hint)

        self.template_name_field = TextField("Имя шаблона")
        body.add_widget(self.template_name_field)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setProperty("class", "TemplateEditorSeparator")
        body.add_widget(separator)

        self.title_field = TextField("Название")
        body.add_widget(self.title_field)

        self.subject_field = TextField("Тема")
        body.add_widget(self.subject_field)

        self.author_field = TextField("Автор")
        body.add_widget(self.author_field)

        self.keywords_label = QLabel("Ключевые слова")
        self.keywords_label.setProperty("class", "FieldLabel")
        body.add_widget(self.keywords_label)

        self.keywords_field = TagEditor()
        self.keywords_field.setPlaceholderText("Один тег на строку")
        body.add_widget(self.keywords_field)

        self.comment_field = TextField("Комментарий")
        body.add_widget(self.comment_field)

        self.copyright_field = TextField("Авторские права")
        body.add_widget(self.copyright_field)

        editor_card.add_widget(body)
        layout.addWidget(editor_card, stretch=1)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.revert_btn = SecondaryButton("Отменить изменения")
        self.revert_btn.clicked.connect(self._revert_changes)
        action_row.addWidget(self.revert_btn)

        action_row.addStretch()

        self.save_btn = PrimaryButton("Сохранить шаблон")
        self.save_btn.setIcon(QIcon(str(resource_path("assets/icons/save.svg"))))
        self.save_btn.clicked.connect(self._save_template)
        action_row.addWidget(self.save_btn)

        layout.addLayout(action_row)
        return panel

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setProperty("class", "TemplateStatusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)

        self.status_label = QLabel("Готово")
        self.status_label.setProperty("class", "TemplateStatusText")
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.field_counter = QLabel("0 тегов · 0 заполненных полей")
        self.field_counter.setProperty("class", "TemplateFieldCounter")
        layout.addWidget(self.field_counter)
        return bar

    def _connect_editor_signals(self) -> None:
        for field in (
            self.template_name_field,
            self.title_field,
            self.subject_field,
            self.author_field,
            self.comment_field,
            self.copyright_field,
        ):
            field.textChanged.connect(self._on_editor_changed)
        self.keywords_field.textChanged.connect(self._on_editor_changed)

    def _refresh_list(self, select_name: str | None = None) -> None:
        self._template_cache.clear()
        self.template_list.blockSignals(True)
        self.template_list.clear()

        names = sorted(TemplateManager.list_templates(), key=str.casefold)
        for name in names:
            try:
                data = TemplateManager.load(name)
            except TemplateError:
                data = {"name": name}
            self._template_cache[name] = data

            keywords = data.get("keywords", [])
            keyword_count = len(keywords) if isinstance(keywords, list) else int(bool(keywords))
            subtitle = data.get("subject") or data.get("title") or "Без описания"
            item = QListWidgetItem(f"{name}\n{subtitle} · {keyword_count} тегов")
            item.setData(Qt.UserRole, name)
            item.setToolTip(name)
            self.template_list.addItem(item)

            if select_name == name:
                item.setSelected(True)
                self.template_list.setCurrentItem(item)

        self.template_list.blockSignals(False)
        self._apply_filter(self.search_field.text())
        self._update_library_summary()
        self._update_action_state()

    def _apply_filter(self, query: str) -> None:
        needle = query.strip().casefold()
        visible = 0
        for index in range(self.template_list.count()):
            item = self.template_list.item(index)
            name = item.data(Qt.UserRole)
            data = self._template_cache.get(name, {})
            searchable = " ".join(
                str(value)
                for value in (
                    name,
                    data.get("title", ""),
                    data.get("subject", ""),
                    data.get("artist", ""),
                    data.get("comment", ""),
                    data.get("copyright", ""),
                    " ".join(data.get("keywords", []))
                    if isinstance(data.get("keywords"), list)
                    else data.get("keywords", ""),
                )
            ).casefold()
            hidden = bool(needle and needle not in searchable)
            item.setHidden(hidden)
            if not hidden:
                visible += 1
        self._update_library_summary(visible)

    def _update_library_summary(self, visible: int | None = None) -> None:
        total = self.template_list.count()
        if visible is None:
            visible = sum(
                not self.template_list.item(index).isHidden()
                for index in range(total)
            )
        if visible == total:
            self.library_summary.setText(f"Шаблонов: {total}")
        else:
            self.library_summary.setText(f"Показано: {visible} из {total}")

    def _on_list_selection_changed(self) -> None:
        item = self.template_list.currentItem()
        if item is None:
            self._update_action_state()
            return

        name = item.data(Qt.UserRole)
        if self._dirty and self.current_template and name != self.current_template:
            answer = QMessageBox.question(
                self,
                "Несохранённые изменения",
                "Переключиться на другой шаблон и потерять изменения?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                self._restore_current_selection()
                return

        self._load_template(name)

    def _restore_current_selection(self) -> None:
        self.template_list.blockSignals(True)
        self.template_list.clearSelection()
        for index in range(self.template_list.count()):
            item = self.template_list.item(index)
            if item.data(Qt.UserRole) == self.current_template:
                self.template_list.setCurrentItem(item)
                item.setSelected(True)
                break
        self.template_list.blockSignals(False)

    def _load_template(self, name: str) -> None:
        try:
            data = TemplateManager.load(name)
        except TemplateError as error:
            self.log(f"Ошибка загрузки: {error}")
            return

        self._loading_editor = True
        self.current_template = name
        self.template_name_field.setText(name)
        self.title_field.setText(data.get("title", ""))
        self.subject_field.setText(data.get("subject", ""))
        self.author_field.setText(data.get("artist", ""))
        keywords = data.get("keywords", [])
        self.keywords_field.setPlainText(
            "\n".join(keywords) if isinstance(keywords, list) else str(keywords or "")
        )
        self.comment_field.setText(data.get("comment", ""))
        self.copyright_field.setText(data.get("copyright", ""))
        self._loading_editor = False

        self._set_dirty(False)
        self.editor_hint.setText(f"Редактируется: {name}")
        self.template_context_changed.emit({"name": name, **data})
        self._update_field_counter()
        self._update_action_state()
        self.log(f"Шаблон '{name}' загружен")

    def _collect_editor_data(self) -> dict:
        keywords = [
            value.strip()
            for value in self.keywords_field.toPlainText().splitlines()
            if value.strip()
        ]
        return {
            "name": self.template_name_field.text().strip(),
            "title": self.title_field.text().strip(),
            "subject": self.subject_field.text().strip(),
            "artist": self.author_field.text().strip(),
            "keywords": keywords,
            "comment": self.comment_field.text().strip(),
            "copyright": self.copyright_field.text().strip(),
        }

    def _on_editor_changed(self, *_args) -> None:
        if self._loading_editor:
            return
        self._set_dirty(True)
        self._update_field_counter()
        self._update_action_state()
        self.template_context_changed.emit(self._collect_editor_data())

    def _set_dirty(self, dirty: bool) -> None:
        self._dirty = dirty
        if dirty:
            self.status_label.setText("Есть несохранённые изменения")
        else:
            self.status_label.setText("Все изменения сохранены")

    def _update_field_counter(self) -> None:
        data = self._collect_editor_data()
        tag_count = len(data["keywords"])
        filled = sum(bool(data[key]) for key in (
            "title", "subject", "artist", "comment", "copyright"
        ))
        self.field_counter.setText(f"{tag_count} тегов · {filled} заполненных полей")

    def _update_action_state(self) -> None:
        has_name = bool(self.template_name_field.text().strip())
        has_selection = self.template_list.currentItem() is not None
        self.save_btn.setEnabled(has_name and self._dirty)
        self.revert_btn.setEnabled(self._dirty)
        self.duplicate_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _save_template(self) -> None:
        data = self._collect_editor_data()
        name = data["name"]
        if not name:
            self.log("Введите имя шаблона")
            self.template_name_field.setFocus()
            return

        old_name = self.current_template
        if old_name and old_name != name and name in TemplateManager.list_templates():
            answer = QMessageBox.question(
                self,
                "Заменить шаблон",
                f"Шаблон '{name}' уже существует. Заменить его?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        try:
            TemplateManager.save(name, data)
            if old_name and old_name != name:
                try:
                    TemplateManager.delete(old_name)
                except TemplateError:
                    pass
            self.current_template = name
            self._set_dirty(False)
            self.editor_hint.setText(f"Редактируется: {name}")
            self._refresh_list(select_name=name)
            self.template_context_changed.emit(data)
            self.log(f"Шаблон '{name}' сохранён")
        except TemplateError as error:
            self.log(f"Ошибка сохранения: {error}")

    def _create_template(self, *_args, log_event: bool = True) -> None:
        if self._dirty and any(self._collect_editor_data().values()):
            answer = QMessageBox.question(
                self,
                "Новый шаблон",
                "Очистить редактор и потерять несохранённые изменения?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        self._loading_editor = True
        for field in (
            self.template_name_field,
            self.title_field,
            self.subject_field,
            self.author_field,
            self.comment_field,
            self.copyright_field,
        ):
            field.clear()
        self.keywords_field.clear()
        self._loading_editor = False

        self.current_template = None
        self.template_list.blockSignals(True)
        self.template_list.clearSelection()
        self.template_list.setCurrentItem(None)
        self.template_list.blockSignals(False)
        self.editor_hint.setText("Новый шаблон")
        self._set_dirty(False)
        self._update_field_counter()
        self._update_action_state()
        self.template_context_changed.emit(self._collect_editor_data())
        self.template_name_field.setFocus()
        if log_event:
            self.log("Создан новый шаблон")

    def _duplicate_template(self) -> None:
        item = self.template_list.currentItem()
        if item is None:
            return
        source_name = item.data(Qt.UserRole)
        try:
            data = TemplateManager.load(source_name)
        except TemplateError as error:
            self.log(f"Ошибка загрузки: {error}")
            return

        existing = set(TemplateManager.list_templates())
        base = f"{source_name} — копия"
        target = base
        number = 2
        while target in existing:
            target = f"{base} {number}"
            number += 1

        data = {**data, "name": target}
        try:
            TemplateManager.save(target, data)
            self._refresh_list(select_name=target)
            self._load_template(target)
            self.log(f"Создана копия шаблона '{source_name}'")
        except TemplateError as error:
            self.log(f"Ошибка дублирования: {error}")

    def _delete_template(self) -> None:
        item = self.template_list.currentItem()
        if item is None:
            self.log("Выберите шаблон для удаления")
            return
        name = item.data(Qt.UserRole)

        answer = QMessageBox.question(
            self,
            "Удалить шаблон",
            f"Удалить шаблон '{name}'? Это действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            TemplateManager.delete(name)
            self.log(f"Шаблон '{name}' удалён")
            self._refresh_list()
            self._create_template(log_event=False)
        except TemplateError as error:
            self.log(f"Ошибка удаления: {error}")

    def _revert_changes(self) -> None:
        if self.current_template:
            self._load_template(self.current_template)
        else:
            self._create_template(log_event=False)
        self.log("Изменения отменены")

    def log(self, message: str) -> None:
        self.log_message.emit(message)
