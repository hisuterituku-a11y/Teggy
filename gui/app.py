from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


class TegiApp(QApplication):
    def __init__(self):
        super().__init__([])
        self.window = MainWindow()
        self.window.show()