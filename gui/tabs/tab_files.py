# gui/tabs/tab_files.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal

class TabFilesWidget(QWidget):
    command_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        self.lbl_file_info = QLabel("Файл: door_mesh.nc (Строк: 1450)")
        self.lbl_file_info.setStyleSheet("font-size: 11px;")
        
        self.btn_preload = QPushButton("Предзагрузка в ESP32")
        self.btn_preload.setStyleSheet("background-color: #004488; font-weight: bold; font-size: 11px; max-height: 24px;")
        
        layout.addWidget(self.lbl_file_info)
        layout.addWidget(self.btn_preload)
