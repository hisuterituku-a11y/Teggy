from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

from core.paths import resource_path
from core.template_manager import TemplateManager
from core.exceptions import TemplateError
from gui.widgets.cards import Card, CardHeader, CardBody
from gui.widgets.inputs import TextField, TagEditor
from gui.widgets.buttons import PrimaryButton, SecondaryButton


class TemplatesPage(QWidget):
    log_message = Signal(str)
    template_context_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "TemplatesPage")
        self.current_template = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        list_card = Card()
        list_header = CardHeader()
        list_header.set_title("Шаблоны")
        list_card.add_widget(list_header)

        list_body = CardBody()
        self.template_list = QListWidget()
        self.template_list.setProperty("class", "TemplateList")
        self.template_list.itemClicked.connect(self._on_template_selected)
        list_body.add_widget(self.template_list)

        list_buttons = QHBoxLayout()
        self.create_btn = SecondaryButton("Создать")
        self.create_btn.clicked.connect(self._create_template)
        list_buttons.addWidget(self.create_btn)

        self.delete_btn = SecondaryButton("Удалить")
        self.delete_btn.clicked.connect(self._delete_template)
        list_buttons.addWidget(self.delete_btn)

        list_body.add_layout(list_buttons)
        list_card.add_widget(list_body)
        left_layout.addWidget(list_card)
        main_layout.addWidget(left_panel, stretch=1)

        right_panel = QWidget()
        right_panel.setFixedWidth(380)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        editor_card = Card()
        editor_header = CardHeader()
        editor_header.set_title("Редактор шаблона")
        editor_card.add_widget(editor_header)

        editor_body = CardBody()
        self.template_name_field = TextField("Имя шаблона")
        editor_body.add_widget(self.template_name_field)

        self.title_field = TextField("Название")
        editor_body.add_widget(self.title_field)

        self.subject_field = TextField("Тема")
        editor_body.add_widget(self.subject_field)

        self.author_field = TextField("Автор")
        editor_body.add_widget(self.author_field)

        self.keywords_field = TagEditor()
        editor_body.add_widget(self.keywords_field)

        self.comment_field = TextField("Комментарий")
        editor_body.add_widget(self.comment_field)

        self.copyright_field = TextField("Авторские права")
        editor_body.add_widget(self.copyright_field)

        editor_card.add_widget(editor_body)
        right_layout.addWidget(editor_card)

        self.save_btn = PrimaryButton("Сохранить шаблон")
        self.save_btn.setIcon(QIcon(str(resource_path("assets/icons/save.svg"))))
        self.save_btn.clicked.connect(self._save_template)
        right_layout.addWidget(self.save_btn)

        right_layout.addStretch()
        main_layout.addWidget(right_panel)

        for field in (
            self.template_name_field,
            self.title_field,
            self.subject_field,
            self.author_field,
            self.comment_field,
            self.copyright_field,
        ):
            field.textChanged.connect(self._emit_editor_context)
        self.keywords_field.textChanged.connect(self._emit_editor_context)

        self._refresh_list()
        self._emit_editor_context()

    def _refresh_list(self):
        self.template_list.clear()
        templates = TemplateManager.list_templates()
        for name in sorted(templates):
            self.template_list.addItem(QListWidgetItem(name))

    def _on_template_selected(self, item):
        name = item.text()
        try:
            data = TemplateManager.load(name)
            self.current_template = name
            self.template_name_field.setText(name)
            self.title_field.setText(data.get("title", ""))
            self.subject_field.setText(data.get("subject", ""))
            self.author_field.setText(data.get("artist", ""))
            keywords = data.get("keywords", [])
            self.keywords_field.setPlainText(
                "\n".join(keywords) if isinstance(keywords, list) else str(keywords)
            )
            self.comment_field.setText(data.get("comment", ""))
            self.copyright_field.setText(data.get("copyright", ""))
            self.template_context_changed.emit({"name": name, **data})
            self.log(f"Шаблон '{name}' загружен")
        except TemplateError as error:
            self.log(f"Ошибка загрузки: {error}")

    def _collect_editor_data(self) -> dict:
        keywords_text = self.keywords_field.toPlainText().strip()
        keywords = [item.strip() for item in keywords_text.splitlines() if item.strip()]
        return {
            "name": self.template_name_field.text().strip() or "Новый шаблон",
            "title": self.title_field.text(),
            "subject": self.subject_field.text(),
            "artist": self.author_field.text(),
            "keywords": keywords,
            "comment": self.comment_field.text(),
            "copyright": self.copyright_field.text(),
        }

    def _emit_editor_context(self, *_args):
        self.template_context_changed.emit(self._collect_editor_data())

    def _save_template(self):
        data = self._collect_editor_data()
        name = data["name"].strip()
        if not name or name == "Новый шаблон":
            self.log("Введите имя шаблона")
            return

        try:
            TemplateManager.save(name, data)
            self.current_template = name
            self.log(f"Шаблон '{name}' сохранён")
            self._refresh_list()
            self.template_context_changed.emit(data)
        except TemplateError as error:
            self.log(f"Ошибка сохранения: {error}")

    def _create_template(self):
        self.template_name_field.clear()
        self.title_field.clear()
        self.subject_field.clear()
        self.author_field.clear()
        self.keywords_field.clear()
        self.comment_field.clear()
        self.copyright_field.clear()
        self.current_template = None
        self.template_list.clearSelection()
        self._emit_editor_context()
        self.log("Новый шаблон")

    def _delete_template(self):
        current_item = self.template_list.currentItem()
        if not current_item:
            self.log("Выберите шаблон для удаления")
            return

        name = current_item.text()
        try:
            TemplateManager.delete(name)
            self.log(f"Шаблон '{name}' удалён")
            self._refresh_list()
            self._create_template()
        except TemplateError as error:
            self.log(f"Ошибка удаления: {error}")

    def log(self, message: str):
        self.log_message.emit(message)
