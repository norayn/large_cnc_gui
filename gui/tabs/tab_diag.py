# gui/tabs/tab_diag.py
from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

class TabDiagWidget(QWidget):
    command_requested = pyqtSignal(str)
    charts_clicked = pyqtSignal() # Специальный сигнал клика по кнопке графиков

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        self.btn_laser = QPushButton("Старт Лазер-Скан")
        self.btn_probe = QPushButton("Старт Щуп-Скан")
        self.btn_charts = QPushButton("Открыть окно графиков отклонений")
        
        for btn in [self.btn_laser, self.btn_probe, self.btn_charts]:
            btn.setStyleSheet("font-size: 11px; max-height: 24px;")
            
        layout.addWidget(self.btn_laser, 0, 0)
        layout.addWidget(self.btn_probe, 0, 1)
        layout.addWidget(self.btn_charts, 1, 0, 1, 2)
        
        self.btn_charts.clicked.connect(self.charts_clicked.emit)
