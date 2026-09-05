# machine_state.py
from PyQt6.QtCore import QObject, pyqtSignal

class CNCMachineState(QObject):
    # Сигнал генерируется всякий раз, когда ЛЮБОЙ параметр станка обновился.
    # Это позволит интерфейсу реактивно перерисовывать DRO и лампочки.
    state_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # --- ФИЗИЧЕСКИЕ И МАШИННЫЕ КООРДИНАТЫ ---
        self.x = 0.000
        self.y = 0.000
        self.z = 0.000
        
        # --- ТЕКУЩИЙ СТАТУС КОНТРОЛЛЕРА ---
        self.status = "DISCONNECTED" # ALARM, IDLE, RUNNING, HOMING, HOLD
        self.is_homed = False
        self.current_line = 0
        self.uptime_ms = 0
        
        # --- ПЕРИФЕРИЯ (ШПИНДЕЛЬ, СОЖ) ---
        self.spindle_on = False
        self.spindle_rpm = 0
        self.coolant_on = False
        self.mist_on = False
        
        # --- СОСТОЯНИЕ РЕЖИМОВ GUI ---
        self.compensation_active = False  # Активна ли матрица Z-высот
        self.alignment_angle = 0.0        # Угол разворота детали в градусах
        self.jog_step = 1.0               # Текущий шаг ручной подачи (0.1, 1.0, 10.0)
        self.jog_feed = 1200              # Текущая скорость ручной подачи
        
        # --- СТАТУС ПОДКЛЮЧЕНИЯ ДАТЧИКОВ ГЕОМЕТРИИ ---
        self.laser_connected = False
        self.probe_connected = False

    def update_telemetry(self, status, x, y, z, is_homed, current_line):
        """Метод обновления данных из сетевого парсера"""
        # Проверяем, изменилось ли что-то действительно, чтобы не спамить перерисовкой UI
        has_changed = (self.status != status or 
                       self.x != x or self.y != y or self.z != z or 
                       self.is_homed != is_homed or self.current_line != current_line)
        
        if has_changed:
            self.status = status
            self.x = x
            self.y = y
            self.z = z
            self.is_homed = is_homed
            self.current_line = current_line
            
            # Оповещаем все подписанные GUI-окна
            self.state_changed.emit()
            
    def set_jog_parameters(self, step=None, feed=None):
        """Метод изменения параметров ручного перемещения из табов"""
        if step is not None: self.jog_step = step
        if feed is not None: self.jog_feed = feed
        self.state_changed.emit()
