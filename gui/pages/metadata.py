from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from gui.widgets.cards import Card, CardHeader, CardBody
from gui.widgets.inputs import TextField, TagEditor
from gui.widgets.buttons import PrimaryButton


class MetadataPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "MetadataPage")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Верхняя панель: выбор папки
        folder_card = Card()
        folder_card.add_widget(QLabel("📁 Папка с фото"))
        # Временное поле
        self.folder_field = TextField("Выберите папку...")
        folder_card.add_widget(self.folder_field)
        main_layout.addWidget(folder_card)

        # Карточка метаданных
        meta_card = Card()
        header = CardHeader()
        header.set_title("Метаданные")
        meta_card.add_widget(header)

        body = CardBody()
        self.title_field = TextField("Название")
        body.add_widget(self.title_field)

        self.subject_field = TextField("Тема")
        body.add_widget(self.subject_field)

        self.comment_field = TextField("Комментарий")
        body.add_widget(self.comment_field)

        self.author_field = TextField("Автор")
        body.add_widget(self.author_field)

        self.copyright_field = TextField("Авторские права")
        body.add_widget(self.copyright_field)

        self.tags_editor = TagEditor()
        body.add_widget(self.tags_editor)

        meta_card.add_widget(body)
        main_layout.addWidget(meta_card)

        # Кнопка
        self.action_btn = PrimaryButton("Записать метаданные")
        main_layout.addWidget(self.action_btn)

        main_layout.addStretch()