from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from core.metadata.metadata_service import MetadataService


class Inspector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Inspector")
        self.setFixedWidth(300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Заголовок
        title = QLabel("Инспектор")
        title.setProperty("class", "InspectorTitle")
        layout.addWidget(title)
        
        # Линия-разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Контейнер для информации
        self.info_container = QWidget()
        self.info_layout = QVBoxLayout(self.info_container)
        self.info_layout.setSpacing(6)
        self.info_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.info_container)
        
        # Словарь для хранения ссылок на виджеты
        self.info_widgets = {}
        
        # Показываем заглушку
        self.show_placeholder()
        
        # Добавляем растяжку
        layout.addStretch()
    
    def show_placeholder(self):
        """Показывает заглушку."""
        self.clear_info()
        placeholder = QLabel("Выберите файл\nдля просмотра информации")
        placeholder.setProperty("class", "InspectorPlaceholder")
        placeholder.setAlignment(Qt.AlignCenter)
        self.info_layout.addWidget(placeholder)
        self.info_widgets['placeholder'] = placeholder
    
    def update_file_info(self, file_info):
        """
        Обновляет информацию о файле в инспекторе.
        
        Args:
            file_info: Объект FileInfo
        """
        self.clear_info()
        
        if not file_info:
            self.show_placeholder()
            return
        
        # Базовая информация
        info = {
            'Имя': file_info.name,
            'Путь': str(file_info.path.parent),
            'Размер': f"{file_info.size_kb:.1f} KB" if file_info.size < 1024*1024 else f"{file_info.size_mb:.1f} MB",
            'Дата изменения': file_info.modified.strftime("%d.%m.%Y %H:%M:%S"),
            'Формат': file_info.extension.upper().replace('.', ''),
        }
        
        # Добавляем информацию о метаданных
        if file_info.extension.lower() in {'.jpg', '.jpeg'}:
            info['Метаданные'] = '✅ Доступны'
            info['Статус'] = 'Готов к чтению/записи'
        else:
            info['Метаданные'] = '⚠️ Будет создан JPG'
            info['Статус'] = 'Требуется конвертация'
        
        # Добавляем виджеты
        for key, value in info.items():
            label = QLabel(f"<b>{key}:</b> {value}")
            label.setProperty("class", "InspectorInfo")
            label.setWordWrap(True)
            self.info_layout.addWidget(label)
            self.info_widgets[key] = label
        
        # Если файл JPG, пытаемся прочитать метаданные
        if file_info.extension.lower() in {'.jpg', '.jpeg'}:
            metadata = MetadataService.read_metadata(str(file_info.path))
            if metadata:
                self.add_separator()
                self.add_metadata_info(metadata)
            else:
                self.add_separator()
                meta_placeholder = QLabel("Метаданные не найдены")
                meta_placeholder.setProperty("class", "InspectorMuted")
                self.info_layout.addWidget(meta_placeholder)
                self.info_widgets['meta_placeholder'] = meta_placeholder
    
    def add_separator(self):
        """Добавляет разделитель."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.info_layout.addWidget(line)
    
    def add_metadata_info(self, metadata: dict):
        """
        Добавляет информацию о метаданных.
        
        Args:
            metadata: Словарь с метаданными
        """
        # Заголовок
        title = QLabel("📋 Метаданные:")
        title.setProperty("class", "InspectorSubtitle")
        self.info_layout.addWidget(title)
        self.info_widgets['meta_title'] = title
        
        # Поля
        fields = {
            'title': 'Title',
            'subject': 'Subject',
            'artist': 'Author',
            'keywords': 'Keywords',
            'comment': 'Comment',
            'copyright': 'Copyright',
            'rating': 'Rating'
        }
        
        for key, display_name in fields.items():
            if key in metadata and metadata[key]:
                value = metadata[key]
                if key == 'keywords' and isinstance(value, list):
                    value = ', '.join(value)
                elif key == 'rating':
                    value = f"{'⭐' * value} ({value}/5)"
                
                label = QLabel(f"<b>{display_name}:</b> {value}")
                label.setProperty("class", "InspectorMetadata")
                label.setWordWrap(True)
                self.info_layout.addWidget(label)
                self.info_widgets[f'meta_{key}'] = label
    
    def clear_info(self):
        """Очищает всю информацию."""
        for widget in self.info_widgets.values():
            self.info_layout.removeWidget(widget)
            widget.deleteLater()
        self.info_widgets.clear()