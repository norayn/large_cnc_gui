# gui/tabs/tab_align.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

class TabAlignWidget(QWidget):
    command_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self.btn_point_a = QPushButton("Точка А")
        self.btn_point_b = QPushButton("Точка В")
        self.btn_apply_align = QPushButton("Применить поворот")
        
        for btn in [self.btn_point_a, self.btn_point_b, self.btn_apply_align]:
            btn.setStyleSheet("font-size: 11px; max-height: 24px;")
            layout.addWidget(btn)
