"""
Загрузка и перекраска SVG-иконок.
"""

from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt


def load_svg_icon(path: Path, color: str) -> QIcon:
    """
    Загружает SVG-файл, заменяет currentColor на указанный цвет.

    Args:
        path: Путь к SVG-файлу
        color: Цвет в формате #RRGGBB

    Returns:
        QIcon: Иконка с новым цветом
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            svg_data = f.read()

        # Заменяем currentColor на цвет темы
        svg_data = svg_data.replace('currentColor', color)

        # Создаём QIcon через QSvgRenderer
        renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    except Exception as e:
        print(f"Ошибка загрузки иконки {path}: {e}")
        return QIcon()