from PySide6.QtCore import QObject, Signal, QEvent
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from pathlib import Path


class DragDropManager(QObject):
    """Централизованный менеджер Drag & Drop для всего приложения."""
    
    folder_dropped = Signal(str)
    files_dropped = Signal(list)  # список путей к файлам
    
    def eventFilter(self, obj, event):
        """Фильтрует события на уровне приложения."""
        if event.type() == QEvent.DragEnter:
            return self._handle_drag_enter(event)
        
        if event.type() == QEvent.Drop:
            return self._handle_drop(event)
        
        return super().eventFilter(obj, event)
    
    def _handle_drag_enter(self, event):
        """Проверяет, можно ли принять перетаскиваемые данные."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return True
        return False
    
    def _handle_drop(self, event):
        """Обрабатывает перетаскивание."""
        urls = event.mimeData().urls()
        if not urls:
            return False
        
        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if not paths:
            return False
        
        # Определяем, что перетащили
        first_path = Path(paths[0])
        
        # Если одна папка
        if len(paths) == 1 and first_path.is_dir():
            self.folder_dropped.emit(str(first_path))
            event.acceptProposedAction()
            return True
        
        # Если файлы
        parent_dir = first_path.parent
        all_same_folder = all(Path(p).parent == parent_dir for p in paths)
        
        if all_same_folder:
            # Проверяем, есть ли изображения
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
            image_paths = [p for p in paths if Path(p).suffix.lower() in image_extensions]
            
            if image_paths:
                self.files_dropped.emit(image_paths)
                event.acceptProposedAction()
                return True
        
        event.ignore()
        return False