from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton

class ControlTabsWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTabWidget::panel { border: 1px solid #3a3a3a; background-color: #222; }
            QTabBar::tab { background: #333; color: #aaa; padding: 4px 10px; font-size: 11px; }
            QTabBar::tab:selected { background: #222; color: #fff; font-weight: bold; }
        """)
        self.init_tabs()
        
    def init_tabs(self):
        # Вкладка 1: JOG
        tab_jog = QWidget()
        jog_grid = QGridLayout(tab_jog)
        jog_grid.setContentsMargins(4, 4, 4, 4)
        jog_grid.addWidget(QLabel("Управление перемещениями портала (Ручной JOG)"), 0, 0)
        self.addTab(tab_jog, "Ручной JOG")
        
        # Вкладка 2: ФАЙЛЫ
        tab_file = QWidget()
        file_layout = QVBoxLayout(tab_file)
        file_layout.setContentsMargins(4, 4, 4, 4)
        self.lbl_file_info = QLabel("Файл: door_mesh.nc (Строк: 1450)")
        self.btn_preload = QPushButton("Предзагрузка в ESP32")
        self.btn_preload.setStyleSheet("background-color: #004488; font-weight: bold; font-size: 11px; max-height: 24px;")
        file_layout.addWidget(self.lbl_file_info)
        file_layout.addWidget(self.btn_preload)
        self.addTab(tab_file, "G-Код Файлы")
        
        # Вкладка 3: ВЫРАВНИВАНИЕ
        tab_align = QWidget()
        align_layout = QHBoxLayout(tab_align)
        align_layout.setContentsMargins(4, 4, 4, 4)
        self.btn_point_a = QPushButton("Точка А")
        self.btn_point_b = QPushButton("Точка В")
        self.btn_apply_align = QPushButton("Применить поворот")
        for btn in [self.btn_point_a, self.btn_point_b, self.btn_apply_align]:
            btn.setStyleSheet("font-size: 11px; max-height: 24px;")
            align_layout.addWidget(btn)
        self.addTab(tab_align, "Выравнивание")
        
        # Вкладка 4: ДИАГНОСТИКА
        tab_diag = QWidget()
        diag_layout = QGridLayout(tab_diag)
        diag_layout.setContentsMargins(4, 4, 4, 4)
        diag_layout.setSpacing(4)
        self.btn_laser = QPushButton("Старт Лазер-Скан")
        self.btn_probe = QPushButton("Старт Щуп-Скан")
        self.btn_charts = QPushButton("Открыть окно графиков отклонений")
        for btn in [self.btn_laser, self.btn_probe, self.btn_charts]:
            btn.setStyleSheet("font-size: 11px; max-height: 24px;")
        diag_layout.addWidget(self.btn_laser, 0, 0)
        diag_layout.addWidget(self.btn_probe, 0, 1)
        diag_layout.addWidget(self.btn_charts, 1, 0, 1, 2)
        self.addTab(tab_diag, "Диагностика")
