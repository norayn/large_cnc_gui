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
        """Тестовый квадрат 200х200 мм (спущен в "модальный" стиль G-кода)"""
        if not self.machine_state: return
        
        # Намеренно убираем повторяющиеся координаты Y, Z и подачу F из кадров 5, 6, 7, 
        # чтобы проверить работу автозаполнения осей в GUI
        self.machine_state.gcode_lines = [
            #"G90 G21",
            "G0 Z5.000 F1500",
            "G0 X0.000 Y0.000",
            "G1 Z-2.000 F300",
            "G1 X200.000 Y0.000 F1200", # Тут заданы полные оси и подача 1200
            "G1 X200.000 Y200.000",     # Пропущена ось Z и скорость F (модальные)
            "G1 X0.000",                 # Пропущены Y, Z и F
            "G1 Y0.000",                 # Пропущены X, Z и F
            "G0 Z5.000",                # Выход фрезы вверх (пропущены X, Y, F)
            "G0 X0.000 Y0.000"          # Возврат в ноль
        ]
        
        self.lbl_file_info.setText(f"Программа: debug_square.nc ({len(self.machine_state.gcode_lines)} кадров)")
        self.btn_preload.setEnabled(True)
        self.gcode_loaded_notify.emit()

    def _preload_gcode_buffer(self):
        """
        ИНТЕЛЛЕКТУАЛЬНЫЙ БИНАРНЫЙ КОМПИЛЯТОР ПОД ПРОТОКОЛ ESP32
        Обеспечивает 100% заполнение всех 5 разделителей ';' за счет кэша модального состояния
        """
        if not self.machine_state: return
        
        # 1. Сигнал старта сессии загрузки
        self.command_requested.emit("GCODE_UPLOAD_START")
        
        # --- КЭШ МОДАЛЬНОГО СОСТОЯНИЯ ТРАЕКТОРИИ ---
        # Если программа начинается не с нуля, берем текущее физическое положение станка из CNCState,
        # чтобы первый кадр не вызвал резкого прыжка моторов
        current_x = self.machine_state.x
        current_y = self.machine_state.y
        current_z = self.machine_state.z
        current_f = 300.0 # Скорость по умолчанию, если не задана в первом кадре
        current_type = 0  # 0=G0 (маршевый), 1=G1 (рабочий)
        
        for idx, line in enumerate(self.machine_state.gcode_lines):
            clean = line.strip().upper()
            if not clean: continue
            
            # Парсим тип интерполяции (модальный параметр)
            if "G0" in clean: current_type = 0
            elif "G1" in clean: current_type = 1
            
            # Ищем координаты регулярными выражениями
            match_x = re.search(r"X([-\d.]+)", clean)
            match_y = re.search(r"Y([-\d.]+)", clean)
            match_z = re.search(r"Z([-\d.]+)", clean)
            match_f = re.search(r"F(\d+)", clean)
            
            # --- ЛОГИКА АВТОЗАПОЛНЕНИЯ ИЗ КЭША GUI ---
            # Если координата найдена в текущей строке — обновляем кэш.
            # Если не найдена — подставляем её последнее известное значение, спасая станок от улета в 0.
            if match_x: current_x = float(match_x.group(1))
            if match_y: current_y = float(match_y.group(1))
            if match_z: current_z = float(match_z.group(1))
            if match_f: current_f = float(match_f.group(1))
            
            # Сборка монолитного пакета: B:cmdType;lineNum;X;Y;Z;F
            # Теперь здесь всегда железно заполнены все 5 разделителей и все параметры!
            packet = f"B:{current_type};{idx};{current_x:.3f};{current_y:.3f};{current_z:.3f};{current_f:.1f}"
            
            # Выталкиваем пакет в поток связи (connection_worker.py добавит \r\n и сделает .flush())
            self.command_requested.emit(packet)
            
        # 2. Сигнал закрытия сессии загрузки
        self.command_requested.emit("GCODE_UPLOAD_END")
        
        for btn in [self.btn_start, self.btn_pause, self.btn_stop]:
            btn.setEnabled(True)
