# gui/tabs/tab_diag.py
from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal

class TabDiagWidget(QWidget):
    command_requested = pyqtSignal(str)
    charts_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Ряд 1: Кнопки автоматических прогонов сканеров (Раздел 6.5)
        scan_layout = QHBoxLayout()
        self.btn_laser_cal = QPushButton("Лазер-Калибровка (Ферма)")
        self.btn_probe_scan = QPushButton("Комплексный Скан (Щуп + Лазер)")
        
        for btn in [self.btn_laser_cal, self.btn_probe_scan]:
            btn.setStyleSheet("font-size: 10px; max-height: 22px; background-color: #2b2b2b;")
        scan_layout.addWidget(self.btn_laser_cal)
        scan_layout.addWidget(self.btn_probe_scan)
        layout.addLayout(scan_layout)
        
        # Ряд 2: Работа с картами компенсации высот Z
        map_layout = QHBoxLayout()
        self.btn_map_export = QPushButton("Выгрузить карту в файл")
        self.btn_map_load = QPushButton("Загрузить карту с ПК")
        for btn in [self.btn_map_export, self.btn_map_load]:
            btn.setStyleSheet("font-size: 10px; max-height: 20px; background-color: #333;")
        map_layout.addWidget(self.btn_map_export)
        map_layout.addWidget(self.btn_map_load)
        layout.addLayout(map_layout)
        
        # Ряд 3: Кнопка вызова окна графиков
        self.btn_charts = QPushButton("ОТКРЫТЬ ОКНО ГРАФИКОВ ОТКЛОНЕНИЙ")
        self.btn_charts.setStyleSheet("font-size: 11px; font-weight: bold; max-height: 24px; background-color: #1a1a3a; color: #00aaff; border: 1px solid #0044aa;")
        layout.addWidget(self.btn_charts)
        
        # --- ПРИВЯЗКА СТРОГИХ КОМАНД ИЗ ВАШЕГО README.MD ---
        # 1. Лазерная калибровка (раздел 6.5)
        self.btn_laser_cal.clicked.connect(lambda: self.command_requested.emit("START_CALIBRATION"))
        # 2. Комплексный скан: старт с 100мм до 3900мм, шаг 50мм, скорость 500 мм/мин
        self.btn_probe_scan.clicked.connect(lambda: self.command_requested.emit("SCAN_GEOMETRY:100;3900;50;500"))
        # 3. Выгрузка CSV карты из ОЗУ чипа
        self.btn_map_export.clicked.connect(lambda: self.command_requested.emit("EXPORT_MAP"))
        
        # Сигнал открытия поп-апа графиков
        self.btn_charts.clicked.connect(self.charts_clicked.emit)
