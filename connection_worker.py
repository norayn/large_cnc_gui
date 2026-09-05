# connection_worker.py
import time
import socket
import re
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot

# Импортируем pyserial для работы по USB. 
# Используем try-except, чтобы скрипт не падал, если библиотека не установлена
try:
    import serial
except ImportError:
    serial = None

class CNCConnectionWorker(QThread):
    # Сигналы для отправки данных обратно в главный GUI-поток
    connection_status = pyqtSignal(bool, str)       # (Успех/Завершено, Сообщение для лога)
    telemetry_received = pyqtSignal(str, float, float, float, bool, bool) # Status, X, Y, Z, Comp, Map
    scan_point_received = pyqtSignal(float, float, str)  # X, Z_val, 'laser' или 'probe'
    log_received = pyqtSignal(str)                  # Сырой текст от станка в общую консоль

    def __init__(self, mode="wifi", wifi_ip="192.168.4.1", wifi_port=8888, serial_port="COM3", baudrate=115200):
        super().__init__()
        self.mode = mode.lower() # "wifi" или "usb"
        self.wifi_ip = wifi_ip
        self.wifi_port = wifi_port
        self.serial_port = serial_port
        self.baudrate = baudrate
        
        self.is_running = True
        self.socket_conn = None
        self.serial_conn = None

    def run(self):
        self.is_running = True
        
        if self.mode == "wifi":
            self._run_wifi()
        elif self.mode == "usb":
            self._run_usb()
        else:
            self.connection_status.emit(False, f"Неизвестный режим связи: {self.mode}")

    # ==========================================
    # ЛОГИКА WI-FI (TCP SOCKET)
    # ==========================================
    def _run_wifi(self):
        try:
            self.log_received.emit(f"Попытка TCP-подключения к {self.wifi_ip}:{self.wifi_port}...")
            self.socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_conn.settimeout(2.0) # Таймаут, чтобы не вешать поток бесконечно
            self.socket_conn.connect((self.wifi_ip, self.wifi_port))
            
            self.connection_status.emit(True, f"Подключено по Wi-Fi к {self.wifi_ip}")
            
            buffer = ""
            while self.is_running:
                try:
                    data = self.socket_conn.recv(1024).decode('utf-8', errors='ignore')
                    if not data:
                        self.connection_status.emit(False, "Wi-Fi соединение закрыто удаленным узлом.")
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        self._parse_incoming_line(line.strip())
                except socket.timeout:
                    continue # Просто проверяем self.is_running и продолжаем ждать
                    
        except Exception as e:
            self.connection_status.emit(False, f"Ошибка Wi-Fi подключения: {e}")
        finally:
            self._close_all()

    # ==========================================
    # ЛОГИКА USB (SERIAL PORT)
    # ==========================================
    def _run_usb(self):
        if serial is None:
            self.connection_status.emit(False, "Ошибка: Библиотека pyserial не установлена!")
            return
            
        try:
            self.log_received.emit(f"Открытие порта {self.serial_port} на скорости {self.baudrate}...")
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baudrate,
                timeout=1.0
            )
            
            # Небольшая пауза для перезагрузки ESP32 при подключении по USB (DTR/RTS)
            time.sleep(1.5) 
            self.serial_conn.reset_input_buffer()
            
            self.connection_status.emit(True, f"Подключено по USB к {self.serial_port}")
            
            buffer = ""
            while self.is_running:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        self._parse_incoming_line(line.strip())
                else:
                    time.sleep(0.01) # Защита от 100% загрузки процессора в цикле ожидания
                    
        except Exception as e:
            self.connection_status.emit(False, f"Ошибка USB подключения: {e}")
        finally:
            self._close_all()

    # ==========================================
    # ПАРСЕР ДАННЫХ ОТ СТАНКА (ОБЩИЙ ДЛЯ ДВУХ РЕЖИМОВ)
    # ==========================================
    def _parse_incoming_line(self, line):
        if not line: return
        
        # Анализируем строку вида: <Status:ALARM|Time=72072|Pos:X=0.00,Y=0.00,Z=0.00|Hom:0|Line=0>
        if line.startswith("<Status:"):
            try:
                # 1. Вытаскиваем статус (ALARM, IDLE, RUNNING и т.д.)
                status = re.search(r"Status:([^|]+)", line).group(1)
                
                # 2. Вытаскиваем координаты X, Y, Z с учетом конструкции X=..., Y=..., Z=...
                x = float(re.search(r"X=([-\d.]+)", line).group(1))
                y = float(re.search(r"Y=([-\d.]+)", line).group(1))
                z = float(re.search(r"Z=([-\d.]+)", line).group(1))
                
                # 3. Вытаскиваем статус хомления (Hom:0 или Hom:1)
                is_homed = int(re.search(r"Hom:(\d+)", line).group(1)) == 1
                
                # 4. Вытаскиваем текущую выполняемую строку (Line=0)
                current_line = int(re.search(r"Line=(\d+)", line).group(1))
                
                # Генерируем сигнал. Поскольку мы убрали флаги Comp и Map из строки ESP32,
                # передаем вместо них статус хомления и номер кадра.
                # Сигнал теперь шлет: (status, x, y, z, is_homed, current_line)
                self.telemetry_received.emit(status, x, y, z, is_homed, current_line)
                
            except (AttributeError, ValueError) as e:
                # Если пакет по дороге побился, выводим ошибку парсинга в лог
                self.log_received.emit(f"Ошибка парсинга пакета: {e} | Строка: {line}")

        elif line.startswith("CONFIG_DATA:"):
            # Просто пробрасываем всю строку в общий лог, 
            # а главный диспетчер main.py передаст её в модель состояния
            self.log_received.emit(line)
            
        # Поток данных сканирования: SCAN:X_val;Z_val;TYPE
        elif line.startswith("SCAN:"):
            try:
                clean_data = line.replace("SCAN:", "")
                parts = clean_data.split(";")
                x = float(parts[0])
                z_val = float(parts[1])
                scan_type = parts[2].lower()
                self.scan_point_received.emit(x, z_val, scan_type)
            except (IndexError, ValueError):
                pass
        else:
            # Все ответы типа "ok" или сообщения от PlatformIO сыпем в общую консоль
            self.log_received.emit(f"Станок: {line}")

    # ==========================================
    # ОТПРАВКА КОМАНД ИЗ GUI В СТАНК
    # ==========================================
    @pyqtSlot(str)
    def send_command(self, cmd_str):
        formatted_cmd = cmd_str.strip() + "\r\n"
        encoded_cmd = formatted_cmd.encode('utf-8')
        
        try:
            if self.mode == "wifi" and self.socket_conn:
                self.socket_conn.sendall(encoded_cmd)
            elif self.mode == "usb" and self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.write(encoded_cmd)
        except Exception as e:
            self.log_received.emit(f"Ошибка при отправке команды [{cmd_str}]: {e}")

    def _close_all(self):
        if self.socket_conn:
            try: self.socket_conn.close() 
            except: pass
            self.socket_conn = None
            
        if self.serial_conn:
            try: self.serial_conn.close() 
            except: pass
            self.serial_conn = None

    def stop(self):
        self.is_running = False
        self._close_all()
        self.wait() # Ждем корректного завершения потока
