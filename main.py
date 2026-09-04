import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QStatusBar, 
                             QPushButton, QLineEdit, QGridLayout)
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import pyqtgraph.opengl as gl

class CNCMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Portal Upper Control HMI [1360x768 Optimized]")
        self.setMinimumSize(1360, 768) # Жесткое ограничение под ноутбук
        self.setStyleSheet("background-color: #1a1a1a; color: #ffffff;")
        
        self.init_ui()
        
    def init_ui(self):
        # Главный вертикальный контейнер
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # ==========================================================
        # 1. ВЕРХНЯЯ ПАНЕЛЬ (Постоянная левая зона + Правые Вкладки)
        # ==========================================================
        top_panel = QHBoxLayout()
        
        # --- СЛЕВА: Постоянная зона контроля (DRO, Статус, Шпиндель) ---
        static_control = QWidget()
        static_control.setStyleSheet("background-color: #262626; border-radius: 4px;")
        static_layout = QHBoxLayout(static_control)
        
        # Блок координат DRO
        dro_layout = QVBoxLayout()
        self.lbl_x = QLabel("X: 0.000")
        self.lbl_y = QLabel("Y: 0.000")
        self.lbl_z = QLabel("Z: 0.000")
        for lbl in [self.lbl_x, self.lbl_y, self.lbl_z]:
            lbl.setStyleSheet("font-family: 'Consolas', monospace; font-size: 20px; color: #00ff00; font-weight: bold;")
        dro_layout.addWidget(self.lbl_x)
        dro_layout.addWidget(self.lbl_y)
        dro_layout.addWidget(self.lbl_z)
        static_layout.addLayout(dro_layout)
        
        # Блок шпинделя и СОЖ
        spindle_layout = QVBoxLayout()
        lbl_spindle_title = QLabel("ШПИНДЕЛЬ / СОЖ")
        lbl_spindle_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        btn_spindle = QPushButton("ШПИНДЕЛЬ [ВЫКЛ]")
        btn_spindle.setStyleSheet("background-color: #3a3a3a; font-size: 11px; padding: 4px;")
        btn_coolant = QPushButton("ОХЛАЖДЕНИЕ [ВЫКЛ]")
        btn_coolant.setStyleSheet("background-color: #3a3a3a; font-size: 11px; padding: 4px;")
        
        spindle_layout.addWidget(lbl_spindle_title)
        spindle_layout.addWidget(btn_spindle)
        spindle_layout.addWidget(btn_coolant)
        static_layout.addLayout(spindle_layout)
        
        top_panel.addWidget(static_control, stretch=1)
        
        # --- СПРАВА: Динамическая зона вкладок управления ---
        self.control_tabs = QTabWidget()
        self.control_tabs.setStyleSheet("""
            QTabWidget::panel { border: 1px solid #3a3a3a; background-color: #222; }
            QTabBar::tab { background: #333; color: #aaa; padding: 6px 12px; font-size: 12px; }
            QTabBar::tab:selected { background: #222; color: #fff; font-weight: bold; }
        """)
        self.init_control_tabs()
        top_panel.addWidget(self.control_tabs, stretch=2)
        
        main_layout.addLayout(top_panel, stretch=1)
        
        # ==========================================================
        # 2. ЦЕНТРАЛЬНАЯ РАБОЧАЯ ЗОНА (Лента G-кода + 3D Визуализатор)
        # ==========================================================
        center_panel = QHBoxLayout()
        
        # Левая колонка: Лента G-кода (~200px)
        self.gcode_zone = QWidget()
        self.gcode_zone.setStyleSheet("background-color: #151515; border: 1px solid #3a3a3a;")
        gcode_layout = QVBoxLayout(self.gcode_zone)
        lbl_gcode = QLabel("ЛЕНТА G-КОДА")
        lbl_gcode.setStyleSheet("font-size: 11px; color: #666; font-weight: bold; font-family: sans-serif;")
        gcode_layout.addWidget(lbl_gcode)
        # Сюда позже добавится QListView для быстрой прокрутки кадров
        gcode_layout.addStickySpacer() if hasattr(gcode_layout, 'addStickySpacer') else gcode_layout.addStretch()
        center_panel.addWidget(self.gcode_zone, stretch=1)
        
        # Правая часть: 3D Окно траектории (растянуто до края экрана)
        self.view_3d = gl.GLViewWidget()
        self.view_3d.setStyleSheet("border: 1px solid #3a3a3a;")
        self.view_3d.setCameraPosition(distance=2500, elevation=30, azimuth=-45)
        
        # Отрисовка сетки нашей 4-метровой станины (4000 х 500 мм)
        grid = gl.GLGridItem()
        grid.setSize(4000, 500, 1)
        grid.setSpacing(100, 100, 0)
        self.view_3d.addItem(grid)
        
        center_panel.addWidget(self.view_3d, stretch=5)
        
        main_layout.addLayout(center_panel, stretch=3)
        
        # ==========================================================
        # 3. НИЖНЯЯ ПАНЕЛЬ (Лог, MDI и Сквозные индикаторы)
        # ==========================================================
        bottom_panel = QHBoxLayout()
        
        self.lbl_log_preview = QLabel("СИСТЕМНЫЙ ЛОГ: Ожидание подключения к ESP32...")
        self.lbl_log_preview.setStyleSheet("font-size: 12px; color: #aaa;")
        bottom_panel.addWidget(self.lbl_log_preview, stretch=3)
        
        # Интегрированная строка MDI команд
        bottom_panel.addWidget(QLabel("MDI:"), stretch=0)
        self.txt_mdi = QLineEdit()
        self.txt_mdi.setStyleSheet("background-color: #000; color: #fff; font-family: monospace; border: 1px solid #555;")
        bottom_panel.addWidget(self.txt_mdi, stretch=2)
        
        # Кнопка открытия глобальных настроек
        btn_settings = QPushButton("НАСТРОЙКИ ЧПУ")
        btn_settings.setStyleSheet("background-color: #555; font-size: 11px; font-weight: bold;")
        bottom_panel.addWidget(btn_settings, stretch=0)
        
        main_layout.addLayout(bottom_panel, stretch=0)
        
        # Глобальный статус-бар со сквозными индикаторами безопасности
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.lbl_comp_status = QLabel(" COMPENSATE: OFF ")
        self.lbl_comp_status.setStyleSheet("background-color: #333; color: #aaa; font-weight: bold; font-size: 11px; margin-right: 5px;")
        self.status_bar.addPermanentWidget(self.lbl_comp_status)
        
        self.lbl_map_status = QLabel(" PROFILE MAP: ACTIVE ")
        self.lbl_map_status.setStyleSheet("background-color: #005500; color: #00ff00; font-weight: bold; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.lbl_map_status)
        
        # Установка центрального виджета
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def init_control_tabs(self):
        # Вкладка 1: JOG
        tab_jog = QWidget()
        jog_grid = QGridLayout(tab_jog)
        jog_grid.setContentsMargins(5, 5, 5, 5)
        jog_grid.addWidget(QLabel("Управление перемещениями портала (Ручной JOG)"), 0, 0, 1, 3)
        # Сюда добавятся кнопки-стрелки
        self.control_tabs.addTab(tab_jog, "Ручной JOG")
        
        # Вкладка 2: ФАЙЛЫ G-КОДА
        tab_file = QWidget()
        file_layout = QVBoxLayout(tab_file)
        file_layout.addWidget(QLabel("Файл: door_mesh.nc (Строк: 1450)"))
        btn_preload = QPushButton("Предзагрузка кода в контроллер (Залить в ESP32)")
        btn_preload.setStyleSheet("background-color: #004488; font-weight: bold;")
        file_layout.addWidget(btn_preload)
        self.control_tabs.addTab(tab_file, "G-Код Файлы")
        
        # Вкладка 3: ВЫРАВНИВАНИЕ (ALIGN)
        tab_align = QWidget()
        align_layout = QHBoxLayout(tab_align)
        align_layout.addWidget(QPushButton("Точка А"))
        align_layout.addWidget(QPushButton("Точка В"))
        align_layout.addWidget(QPushButton("Применить поворот"))
        self.control_tabs.addTab(tab_align, "Выравнивание")
        
        # Вкладка 4: ДИАГНОСТИКА И СКАНЕРЫ
        tab_diag = QWidget()
        diag_layout = QGridLayout(tab_diag)
        diag_layout.addWidget(QPushButton("Старт Лазер-Скан"), 0, 0)
        diag_layout.addWidget(QPushButton("Старт Щуп-Скан"), 0, 1)
        diag_layout.addWidget(QPushButton("Открыть окно графиков отклонений"), 1, 0, 1, 2)
        self.control_tabs.addTab(tab_diag, "Диагностика")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CNCMainWindow()
    window.show()
    sys.exit(app.exec())
