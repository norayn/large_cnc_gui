# machine_state.py
from PyQt6.QtCore import QObject, pyqtSignal

class CNCMachineState(QObject):
    state_changed = pyqtSignal()
    config_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # Рабочие координаты (WCS), приходящие в телеметрии
        self.x = 0.000
        self.y = 0.000
        self.z = 0.000
        
        # Рассчитанные машинные координаты (MCS)
        self.m_x = 0.000
        self.m_y = 0.000
        self.m_z = 0.000
        
        # Смещения рабочих координат относительно машинного нуля
        self.offset_x = 0.000
        self.offset_y = 0.000
        self.offset_z = 0.000
        
        self.status = "DISCONNECTED"
        self.is_homed = False
        self.current_line = 0
        
        self.config = {}

        self.gcode_lines = []

    def update_telemetry(self, status, x, y, z, is_homed, current_line):
        has_changed = (self.status != status or 
                       self.x != x or self.y != y or self.z != z or 
                       self.is_homed != is_homed or self.current_line != current_line)
        if has_changed:
            self.status = status
            self.x = x
            self.y = y
            self.z = z
            
            # Математический расчет MCS на основе текущих WCS и загруженных офсетов
            self.m_x = self.x + self.offset_x
            self.m_y = self.y + self.offset_y
            self.m_z = self.z + self.offset_z
            
            self.is_homed = is_homed
            self.current_line = current_line
            self.state_changed.emit()

    def parse_config_string(self, config_raw):
        try:
            clean_str = config_raw.replace("CONFIG_DATA:", "").strip()
            if not clean_str: return
            
            pairs = clean_str.split(";")
            for pair in pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    k_str = key.strip()
                    v_str = value.strip()
                    
                    self.config[k_str] = v_str
                    
                    # ПЕРЕХВАТ СМЕЩЕНИЙ ИЗ КОНФИГА: Переводим во float для математики
                    if k_str == "wcsOffsetX": self.offset_x = float(v_str)
                    elif k_str == "wcsOffsetY": self.offset_y = float(v_str)
                    elif k_str == "wcsOffsetZ": self.offset_z = float(v_str)
            
            # После изменения офсетов — принудительно пересчитываем MCS для текущей точки
            self.m_x = self.x + self.offset_x
            self.m_y = self.y + self.offset_y
            self.m_z = self.z + self.offset_z
            
            self.config_updated.emit()
            self.state_changed.emit()
        except Exception:
            pass
