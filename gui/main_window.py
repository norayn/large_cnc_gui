# gui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QStatusBar, QPushButton, QLineEdit)
from PyQt6.QtCore import Qt

# Импортируем соседние модули из этой же папки gui
from gui.static_control import StaticControlWidget
from gui.control_tabs import ControlTabsWidget
from gui.gcode_list import GCodeListWidget
from gui.visualizer_3d import CNCVisualizer3D

class CNCMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Portal Upper Control HMI [Modular 1260x700]")
        self.setMinimumSize(1260, 700) 
        self.resize(1260, 700)
        self.setStyleSheet("background-color: #1a1a1a; color: #ffffff;")
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # ==========================================================
        # 1. ВЕРХНЯЯ ПАНЕЛЬ
        # ==========================================================
        top_panel = QHBoxLayout()
        top_panel.setSpacing(4)
        
        self.static_control = StaticControlWidget()
        self.control_tabs = ControlTabsWidget()
        
        top_panel.addWidget(self.static_control, stretch=1)
        top_panel.addWidget(self.control_tabs, stretch=2)
        main_layout.addLayout(top_panel, stretch=1)
        
        # ==========================================================
        # 2. ЦЕНТРАЛЬНАЯ РАБОЧАЯ ЗОНА (Пропорции скорректированы)
        # ==========================================================
        center_panel = QHBoxLayout()
        center_panel.setSpacing(4)
        
        self.gcode_zone = GCodeListWidget()
        self.view_3d = CNCVisualizer3D()
        
        # Пропорция изменена с (2 и 5) на (3 и 10). 
        # Лента G-кода стала уже примерно на 30%, освободив место для 3D вида.
        center_panel.addWidget(self.gcode_zone, stretch=3) 
        center_panel.addWidget(self.view_3d, stretch=10)
        main_layout.addLayout(center_panel, stretch=4)
        
        # ==========================================================
        # 3. НИЖНЯЯ ПАНЕЛЬ И СТАТУС-БАР (С кнопкой ТЕРМИНАЛ)
        # ==========================================================
        bottom_panel = QHBoxLayout()
        bottom_panel.setSpacing(4)
        
        self.lbl_log_preview = QLabel("ЛОГ: Система инициализирована. Потоковое логирование активно.")
        self.lbl_log_preview.setStyleSheet("font-size: 11px; color: #aaa;")
        bottom_panel.addWidget(self.lbl_log_preview, stretch=3)
        
        bottom_panel.addWidget(QLabel("MDI:"), stretch=0)
        self.txt_mdi = QLineEdit()
        self.txt_mdi.setStyleSheet("background-color: #000; color: #fff; font-family: monospace; border: 1px solid #555; font-size: 11px; max-height: 20px;")
        bottom_panel.addWidget(self.txt_mdi, stretch=2)
        
        self.btn_open_terminal = QPushButton("ТЕРМИНАЛ")
        self.btn_open_terminal.setStyleSheet("background-color: #1a3a1a; color: #00ff00; font-size: 10px; font-weight: bold; max-height: 20px; padding: 2px 8px; border: 1px solid #005500;")
        bottom_panel.addWidget(self.btn_open_terminal, stretch=0)
        
        self.btn_settings = QPushButton("НАСТРОЙКИ")
        self.btn_settings.setStyleSheet("background-color: #555; font-size: 10px; font-weight: bold; max-height: 20px; padding: 2px 10px;")
        bottom_panel.addWidget(self.btn_settings, stretch=0)
        main_layout.addLayout(bottom_panel, stretch=0)
        
        # Статус-бар со сквозными индикаторами безопасности
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("max-height: 18px;")
        self.setStatusBar(self.status_bar)
        
        self.lbl_comp_status = QLabel(" COMPENSATE: OFF ")
        self.lbl_comp_status.setStyleSheet("background-color: #333; color: #aaa; font-weight: bold; font-size: 10px; margin-right: 4px;")
        self.status_bar.addPermanentWidget(self.lbl_comp_status)
        
        self.lbl_map_status = QLabel(" PROFILE MAP: ACTIVE ")
        self.lbl_map_status.setStyleSheet("background-color: #005500; color: #00ff00; font-weight: bold; font-size: 10px;")
        self.status_bar.addPermanentWidget(self.lbl_map_status)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
