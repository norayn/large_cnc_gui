# gui/tabs/tab_files.py
import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal

class TabFilesWidget(QWidget):
    command_requested = pyqtSignal(str)
    gcode_loaded_notify = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.machine_state = None
        self.init_ui()

    def set_state_reference(self, state_obj):
        self.machine_state = state_obj

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        self.lbl_file_info = QLabel("Программа: [Нет данных]")
        self.lbl_file_info.setStyleSheet("font-size: 11px; font-weight: bold; color: #aaa;")
        layout.addWidget(self.lbl_file_info)
        
        upper_btns = QHBoxLayout()
        btn_generate_square = QPushButton("Загрузить Тест-Квадрат 200мм")
        btn_generate_square.setStyleSheet("background-color: #333; font-size: 10px; max-height: 22px;")
        btn_generate_square.clicked.connect(self._generate_test_square)
        
        self.btn_preload = QPushButton("Залить буфер в ESP32")
        self.btn_preload.setEnabled(False)
        self.btn_preload.setStyleSheet("background-color: #004488; font-weight: bold; font-size: 10px; max-height: 22px; color: #fff;")
        self.btn_preload.clicked.connect(self._preload_gcode_buffer)
        
        upper_btns.addWidget(btn_generate_square)
        upper_btns.addWidget(self.btn_preload)
        layout.addLayout(upper_btns)
        
        cycle_btns = QHBoxLayout()
        self.btn_start = QPushButton("СТАРТ")
        self.btn_pause = QPushButton("ПАУЗА")
        self.btn_stop = QPushButton("СТОП")
        
        self.btn_start.setStyleSheet("background-color: #005500; font-weight: bold; font-size: 11px; max-height: 24px;")
        self.btn_pause.setStyleSheet("background-color: #444400; font-weight: bold; font-size: 11px; max-height: 24px;")
        self.btn_stop.setStyleSheet("background-color: #550000; font-weight: bold; font-size: 11px; max-height: 24px;")
        
        self.btn_start.clicked.connect(lambda: self.command_requested.emit("START_PROGRAM"))
        self.btn_pause.clicked.connect(lambda: self.command_requested.emit("FEED_HOLD"))
        self.btn_stop.clicked.connect(lambda: self.command_requested.emit("RESET_ALARM"))
        
        for btn in [self.btn_start, self.btn_pause, self.btn_stop]:
            btn.setEnabled(False)
            cycle_btns.addWidget(btn)
        layout.addLayout(cycle_btns)

    def _generate_test_square(self):
        """
        Инженерный полигон для тестированияLook-Ahead и Junction Deviation.
        Программа на 16 кадров с поворотами под углами 15, 45, 60, 90 и 120 градусов.
        """
        if not self.machine_state: return
        
        # Генерируем массив траектории (все линейные перемещения G1 идут на подаче F1500)
        self.machine_state.gcode_lines = [
            "G90 G21",                      # Кадр 0: Инициализация (Абсолют, мм)
            "G0 Z5.000 F2000",              # Кадр 1: Безопасный подъем Z вверх
            "G0 X0.000 Y0.000",             # Кадр 2: Выход в локальный рабочий ноль
            "G1 Z-2.000 F300",              # Кадр 3: Заглубление фрезы на 2 мм
            
            # --- СЕГМЕНТ 1: Поворот под 15 градусов ---
            "G1 X100.000 Y0.000 F1500",     # Кадр 4: Прямая линия по оси X
            "G1 X196.590 Y25.880",          # Кадр 5: Плавный излом на 15° (длина 100мм)
            
            # --- СЕГМЕНТ 2: Поворот под 45 градусов ---
            "G1 X267.300 Y96.590",          # Кадр 6: Переход на диагональ под 45°
            
            # --- СЕГМЕНТ 3: Поворот под 60 градусов ---
            "G1 X267.300 Y200.000",         # Кадр 7: Излом на 60° (каретка идет строго по Y)
            
            # --- СЕГМЕНТ 4: Прямой угол 90 градусов ---
            "G1 X100.000 Y200.000",         # Кадр 8: Поворот на 90° (возврат по оси X)
            
            # --- СЕГМЕНТ 5: Острый разворот 120 градусов (Шпилька) ---
            "G1 X50.000 Y113.400",          # Кадр 9: Идем по диагонали назад-вниз
            "G1 X0.000 Y200.000",           # Кадр 10: Жесткий излом на 120° (резко вверх-влево)
            
            # --- СЕГМЕНТ 6: Замыкание контура и выход ---
            "G1 X0.000 Y100.000",           # Кадр 11: Опускаемся по Y
            "G1 X50.000 Y50.000",           # Кадр 12: Небольшой зигзаг
            "G1 X0.000 Y0.000",             # Кадр 13: Возврат в точку старта
            
            "G0 Z5.000 F2000",              # Кадр 14: Выход фрезы из материала
            "G0 X0.000 Y0.000"              # Кадр 15: Отвод портала в ноль
        ]
        
        self.lbl_file_info.setText(f"Программа: lookahead_test_poly.nc ({len(self.machine_state.gcode_lines)} кадров)")
        self.btn_preload.setEnabled(True)
        
        # Сигнал для обновления Ленты G-кода на экране ноутбука
        self.gcode_loaded_notify.emit()



    def _preload_gcode_buffer(self):
        """
        Новая логика пакетной загрузки программы.
        Вызывает модуль математического Look-Ahead планировщика ЧПУ.
        """
        if not self.machine_state or not self.machine_state.gcode_lines: 
            return
            
        # Импортируем наш новый планировщик
        from gcode.core_planner import CNCPlannerX
        
        # Инстанцируем планировщик. 
        # Параметры accel и junction_deviation в будущем можно брать прямо из state.config!
        planner = CNCPlannerX(accel=150.0, min_speed=2.0, junction_deviation=0.02)
        
        # 1. Открываем сессию бинарной загрузки в ESP32
        self.command_requested.emit("GCODE_UPLOAD_START")
        
        # 2. Передаем исходные строки G-кода в математический планировщик Look-Ahead.
        # Получаем готовый массив строк B:... с расчитанными v_start и v_end и 7 разделителями!
        binary_packets = planner.parse_and_plan(self.machine_state.gcode_lines)
        
        # 3. Выплескиваем скомпилированный поток пакетов в воркер связи
        for packet in binary_packets:
            self.command_requested.emit(packet)
            
        # 4. Закрываем сессию загрузки программы
        self.command_requested.emit("GCODE_UPLOAD_END")
        
        # Активируем кнопки цикла СТАРТ/ПАУЗА на ноутбуке
        for btn in [self.btn_start, self.btn_pause, self.btn_stop]:
            btn.setEnabled(True)
