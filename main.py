# main.py
import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import CNCMainWindow
from connection_worker import CNCConnectionWorker

class CNCApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = CNCMainWindow()
        self.conn_worker = None
        
        # Пример запуска соединения (в будущем параметры будут браться из окна "НАСТРОЙКИ")
        # Вы можете вручную поменять mode="wifi" или mode="usb" для тестов
        #self.start_connection(mode="wifi", ip="192.168.4.1", port=8888)
        self.start_connection(mode="usb", com="COM4", baud=115200)

        # Перехватываем событие закрытия главного окна, чтобы безопасно остановить потоки и порт
        self.window.closeEvent = self.on_window_close

    def start_connection(self, mode="wifi", ip="192.168.4.1", port=8888, com="COM3", baud=115200):
        # Если старый поток запущен — останавливаем его
        if self.conn_worker and self.conn_worker.isRunning():
            self.conn_worker.stop()
            
        # Создаем новый поток связи с нужными параметрами
        self.conn_worker = CNCConnectionWorker(
            mode=mode, wifi_ip=ip, wifi_port=port, serial_port=com, baudrate=baud
        )
        
        # --- СВЯЗЫВАНИЕ СИГНАЛОВ (ПОТОК -> ИНТЕРФЕЙС) ---
        # 1. Прием логов и ошибок
        self.conn_worker.log_received.connect(
            lambda msg: self.window.lbl_log_preview.setText(f"ЛОГ: {msg}")
        )
        # 2. Обновление статуса соединения
        self.conn_worker.connection_status.connect(self.handle_connection_status)
        
        # 3. Обновление координат (DRO) при получении телеметрии
        self.conn_worker.telemetry_received.connect(self.handle_telemetry)
        
        # Запускаем поток на выполнение
        self.conn_worker.start()

    def handle_connection_status(self, success, message):
        self.window.lbl_log_preview.setText(f"ЛОГ: {message}")
        if success:
            self.window.status_bar.showMessage("Станок готов к работе", 5000)
        else:
            self.window.status_bar.showMessage("Ошибка связи!", 5000)

    def handle_telemetry(self, status, x, y, z, is_homed, current_line):
        # 1. Передаем координаты в наш изолированный GUI-модуль DRO
        self.window.static_control.update_coordinates(x, y, z)
        
        # 2. Динамически меняем заголовок окна ноутбука, показывая статус и текущий кадр G-кода
        self.window.setWindowTitle(f"CNC Portal Upper Control HMI [Статус: {status} | Кадр: {current_line}]")
        
        # 3. Управляем сквозным индикатором привязки к дому (Hom) вместо компенсаций
        if is_homed:
            self.window.lbl_comp_status.setText(" MACHINE: HOMED ")
            self.window.lbl_comp_status.setStyleSheet("background-color: #00ff00; color: #000; font-weight: bold; font-size: 10px; margin-right: 4px;")
        else:
            self.window.lbl_comp_status.setText(" MACHINE: NOT HOMED ")
            self.window.lbl_comp_status.setStyleSheet("background-color: #aa0000; color: #fff; font-weight: bold; font-size: 10px; margin-right: 4px;")
            
        # Если статус станка ALARM — подсветим лог превью тревожным цветом
        if status == "ALARM":
            self.window.lbl_log_preview.setStyleSheet("font-size: 11px; color: #ff3333; font-weight: bold;")
            self.window.lbl_log_preview.setText("ЛОГ: Внимание! Сработал режим тревоги (ALARM). Требуется сброс.")


    def on_window_close(self, event):
        # Метод сработает при закрытии крестиком ноутбука. Закрываем порты чисто.
        if self.conn_worker:
            self.conn_worker.stop()
        event.accept()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    cnc_app = CNCApplication()
    cnc_app.run()
