# gui/tabs/tab_jog.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QSlider
from PyQt6.QtCore import pyqtSignal, Qt

class TabJogWidget(QWidget):
    # Сигнал для отправки сформированной команды в станок через main.py
    command_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.machine_state = None 
        
        # Значения по умолчанию для перемещений
        self.selected_step = 1.0     # мм
        self.selected_feed = 1200    # мм/мин
        
        self.init_ui()

    def set_state_reference(self, state_obj):
        """Получение ссылки на Единый Источник Истины для расчета абсолютных координат"""
        self.machine_state = state_obj

    def init_ui(self):
        # Главный горизонтальный контейнер вкладки
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(8)

        # ==========================================
        # БЛОК 1: КРЕСТ ПЕРЕМЕЩЕНИЙ (X/Y/Z)
        # ==========================================
        motion_group = QWidget()
        motion_layout = QHBoxLayout(motion_group)
        motion_layout.setContentsMargins(0, 0, 0, 0)
        motion_layout.setSpacing(4)

        # Сетка для X и Y
        xy_grid = QGridLayout()
        xy_grid.setSpacing(2)
        
        btn_y_plus  = QPushButton("Y+")
        btn_x_minus = QPushButton("X-")
        btn_x_plus  = QPushButton("X+")
        btn_y_minus = QPushButton("Y-")
        
        for btn in [btn_y_plus, btn_x_minus, btn_x_plus, btn_y_minus]:
            btn.setStyleSheet("font-weight: bold; font-size: 11px; min-width: 42px; max-width: 42px; max-height: 24px; background-color: #333;")
            
        xy_grid.addWidget(btn_y_plus, 0, 1)
        xy_grid.addWidget(btn_x_minus, 1, 0)
        xy_grid.addWidget(btn_x_plus, 1, 2)
        xy_grid.addWidget(btn_y_minus, 2, 1)
        motion_layout.addLayout(xy_grid)

        # Вертикаль для Z
        z_layout = QVBoxLayout()
        z_layout.setSpacing(2)
        btn_z_plus = QPushButton("Z+")
        btn_z_minus = QPushButton("Z-")
        for btn in [btn_z_plus, btn_z_minus]:
            btn.setStyleSheet("font-weight: bold; font-size: 11px; min-width: 40px; max-width: 40px; max-height: 24px; background-color: #3b3b3b; color: #ffaa00;")
        z_layout.addWidget(btn_z_plus)
        z_layout.addWidget(btn_z_minus)
        motion_layout.addLayout(z_layout)

        main_layout.addWidget(motion_group)

        # ==========================================
        # БЛОК 2: ВЫБОР ШАГА И СКОРОСТИ ПОДАЧИ
        # ==========================================
        settings_group = QWidget()
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(2)

        # Радио-кнопки выбора дискретного шага
        step_label = QLabel("ШАГ (мм):")
        step_label.setStyleSheet("font-size: 9px; color: #888; font-weight: bold;")
        settings_layout.addWidget(step_label)

        step_btn_layout = QHBoxLayout()
        self.step_group = QButtonGroup(self)
        
        steps = [0.1, 1.0, 10.0, 100.0]
        for idx, s_val in enumerate(steps):
            rb = QRadioButton(str(s_val))
            rb.setStyleSheet("font-size: 10px; color: #ccc;")
            if s_val == 1.0: rb.setChecked(True)
            self.step_group.addButton(rb, idx)
            step_btn_layout.addWidget(rb)
        self.step_group.idClicked.connect(self._handle_step_change)
        settings_layout.addLayout(step_btn_layout)

        # Ползунок скорости подачи JOG
        self.lbl_feed = QLabel("ПОДАЧА: 1200 мм/мин")
        self.lbl_feed.setStyleSheet("font-size: 9px; color: #888; font-weight: bold;")
        settings_layout.addWidget(self.lbl_feed)

        self.slider_feed = QSlider(Qt.Orientation.Horizontal)
        self.slider_feed.setRange(100, 3000)
        self.slider_feed.setValue(1200)
        self.slider_feed.setStyleSheet("max-height: 15px;")
        self.slider_feed.valueChanged.connect(self._handle_feed_change)
        settings_layout.addWidget(self.slider_feed)

        main_layout.addWidget(settings_group, stretch=1)

        # ==========================================
        # БЛОК 3: ОБНУЛЕНИЕ КООРДИНАТ И БАЗИРОВАНИЕ
        # ==========================================
        wcs_group = QWidget()
        wcs_layout = QGridLayout(wcs_group)
        wcs_layout.setContentsMargins(0, 0, 0, 0)
        wcs_layout.setSpacing(2)

        btn_zero_x = QPushButton("Zero X")
        btn_zero_y = QPushButton("Zero Y")
        btn_zero_z = QPushButton("Zero Z")
        btn_zero_all = QPushButton("ZERO ALL")
        btn_home = QPushButton("HOME ($H)")

        for btn in [btn_zero_x, btn_zero_y, btn_zero_z]:
            btn.setStyleSheet("font-size: 10px; max-height: 20px; background-color: #444;")
        btn_zero_all.setStyleSheet("font-size: 10px; font-weight: bold; max-height: 20px; background-color: #005500; color: #fff;")
        btn_home.setStyleSheet("font-size: 10px; font-weight: bold; max-height: 20px; background-color: #004488; color: #fff;")

        wcs_layout.addWidget(btn_zero_x, 0, 0)
        wcs_layout.addWidget(btn_zero_y, 0, 1)
        wcs_layout.addWidget(btn_zero_z, 1, 0)
        wcs_layout.addWidget(btn_zero_all, 1, 1)
        wcs_layout.addWidget(btn_home, 2, 0, 1, 2)

        main_layout.addWidget(wcs_group)

        # ==========================================
        # БЛОК 4: СЕРВИСНЫЕ И ОТЛАДОЧНЫЕ КНОПКИ (ОБНОВЛЕНО)
        # ==========================================
        service_group = QWidget()
        service_layout = QVBoxLayout(service_group)
        service_layout.setContentsMargins(0, 0, 0, 0)
        service_layout.setSpacing(3)

        self.btn_homed_debug = QPushButton("SET_HOMED_DEBUG")
        self.btn_homed_debug.setStyleSheet("""
            background-color: #884400; color: #ffffff; font-weight: bold; 
            font-size: 10px; padding: 3px; max-height: 22px; border: 1px solid #ffaa00;
        """)
        
        self.btn_reset_alarm = QPushButton("СБРОС АВАРИИ")
        self.btn_reset_alarm.setStyleSheet("""
            background-color: #aa0000; color: #ffffff; font-weight: bold; 
            font-size: 10px; padding: 3px; max-height: 22px; border: 1px solid #ff3333;
        """)
        
        service_layout.addWidget(self.btn_homed_debug)
        service_layout.addWidget(self.btn_reset_alarm)
        service_layout.addStretch()
        
        main_layout.addWidget(service_group)

        # ==========================================
        # СИНХРОНИЗАЦИЯ С КОМАНДАМИ ПРОТОКОЛА
        # ==========================================
        btn_x_plus.clicked.connect(lambda: self._send_jog_command("X", 1))
        btn_x_minus.clicked.connect(lambda: self._send_jog_command("X", -1))
        btn_y_plus.clicked.connect(lambda: self._send_jog_command("Y", 1))
        btn_y_minus.clicked.connect(lambda: self._send_jog_command("Y", -1))
        btn_z_plus.clicked.connect(lambda: self._send_jog_command("Z", 1))
        btn_z_minus.clicked.connect(lambda: self._send_jog_command("Z", -1))

        # Привязка сервисных команд строго по паспорту проекта
        btn_zero_x.clicked.connect(lambda: self.command_requested.emit("SET_ZERO:X"))
        btn_zero_y.clicked.connect(lambda: self.command_requested.emit("SET_ZERO:Y"))
        btn_zero_z.clicked.connect(lambda: self.command_requested.emit("SET_ZERO:Z"))
        btn_zero_all.clicked.connect(lambda: self.command_requested.emit("SET_ZERO:ALL"))
        btn_home.clicked.connect(lambda: self.command_requested.emit("$H"))
        
        self.btn_homed_debug.clicked.connect(lambda: self.command_requested.emit("SET_HOMED_DEBUG"))
        self.btn_reset_alarm.clicked.connect(lambda: self.command_requested.emit("RESET_ALARM"))

    def _handle_step_change(self, btn_id):
        steps = [0.1, 1.0, 10.0, 100.0]
        self.selected_step = steps[btn_id]

    def _handle_feed_change(self, value):
        self.selected_feed = value
        self.lbl_feed.setText(f"ПОДАЧА: {value} мм/мин")

    def _send_jog_command(self, axis, direction):
        if not self.machine_state:
            return 
            
        current_pos = 0.0
        if axis == "X": current_pos = self.machine_state.x
        elif axis == "Y": current_pos = self.machine_state.y
        elif axis == "Z": current_pos = self.machine_state.z

        target_pos = current_pos + (self.selected_step * direction)

        # Формат по ТЗ: JOG:G1 X160.000 F1500
        jog_cmd = f"JOG:G1 {axis}{target_pos:.3f} F{self.selected_feed}"
        self.command_requested.emit(jog_cmd)
