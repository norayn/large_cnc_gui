# main.py
import sys
import datetime
from PyQt6.QtWidgets import QApplication

# Импортируем модули
from gui.main_window import CNCMainWindow
from gui.dialog_log import CNCLogWindow # Новый импорт окна логов
from connection_worker import CNCConnectionWorker
from machine_state import CNCMachineState
from gui.dialog_settings import CNCSettingsDialog # Добавляем импорт нового окна

class CNCApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.log_file_path = "cnc_session.log"
        self.conn_worker = None
        
        self.state = CNCMachineState()
        self.window = CNCMainWindow()
        self.log_window = CNCLogWindow(log_path=self.log_file_path, parent=self.window)
        
        # Инициализируем модальное окно настроек и передаем ссылку на состояние
        self.settings_dialog = CNCSettingsDialog(state_obj=self.state, parent=self.window)
        
        self.window.control_tabs.tab_jog.set_state_reference(self.state)
        self.state.state_changed.connect(self.sync_gui_with_state)
        
        self.window.btn_open_terminal.clicked.connect(self.log_window.show)
        
        # Привязка кнопки НАСТРОЙКИ из нижней панели к выводу модального окна
        self.window.btn_settings.clicked.connect(self.handle_open_settings)
        # Связываем отправку команд сохранения из окна настроек с потоком связи
        self.settings_dialog.config_change_requested.connect(self.handle_gui_command_request)
        
        self.start_connection(mode="usb", com="COM4", baud=115200)
        self.window.closeEvent = self.on_window_close

    def handle_connection_status(self, success, message):
        self.write_to_log_file("[SYSTEM]", message)
        self.window.lbl_log_preview.setStyleSheet("font-size: 11px; color: #aaa;")
        self.window.lbl_log_preview.setText(f"ЛОГ СВЯЗИ: {message}")
        
        # АВТОЗАПРОС КОНФИГОВ ПРИ УСПЕШНОМ ПОДКЛЮЧЕНИИ
        if success and self.conn_worker:
            self.write_to_log_file("[GUI -> ЧПУ]", "GET_CONFIG")
            self.conn_worker.send_command("GET_CONFIG")

    def handle_incoming_log(self, msg):
        """Перехват текстовых сообщений от ESP32"""
        self.write_to_log_file("[ЧПУ -> GUI]", msg)
        
        # Если пришла строка конфигурационных данных - скармливаем ее модели состояния
        if msg.startswith("CONFIG_DATA:"):
            self.state.parse_config_string(msg)
            self.window.lbl_log_preview.setStyleSheet("font-size: 11px; color: #00ffff;")
            self.window.lbl_log_preview.setText("ЛОГ: Конфигурационные параметры успешно считаны из памяти ЧПУ.")
        else:
            self.window.lbl_log_preview.setStyleSheet("font-size: 11px; color: #00ff00;")
            self.window.lbl_log_preview.setText(f"ОТВЕТ СТАНКА: {msg}")

    def start_connection(self, mode="usb", ip="192.168.4.1", port=8888, com="COM4", baud=115200):
        if self.conn_worker and self.conn_worker.isRunning():
            self.conn_worker.stop()
            
        self.conn_worker = CNCConnectionWorker(
            mode=mode, wifi_ip=ip, wifi_port=port, serial_port=com, baudrate=baud
        )
        
        # Изменяем перехват лога: теперь он идет в метод файлового логирования
        self.conn_worker.log_received.connect(self.handle_incoming_log)
        self.conn_worker.connection_status.connect(self.handle_connection_status)
        
        # Перехватываем телеметрию. Дополнительно пишем ее в файл (опционально, можно закомментировать для чистоты)
        self.conn_worker.telemetry_received.connect(self.handle_telemetry_packet)
        
        self.window.control_tabs.command_requested.connect(self.handle_gui_command_request)
        self.window.txt_mdi.returnPressed.connect(self.handle_mdi_send)

        self.conn_worker.start()

    def write_to_log_file(self, direction, text):
        """Потоковая запись строки на диск в режиме Append и проброс в открытое окно"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] {direction} {text}"
        
        # Мгновенная запись на диск (без удержания файла в RAM)
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception:
            pass
            
        # Пробрасываем строчку в окно терминала логов (выведется, только если окно открыто)
        self.log_window.append_log_line(log_line)

    def handle_gui_command_request(self, cmd):
        """Перехват команд от графических вкладок (JOG, кнопки)"""
        if self.conn_worker:
            self.write_to_log_file("[GUI -> ЧПУ]", cmd)
            self.conn_worker.send_command(cmd)

    def handle_mdi_send(self):
        """Отправка команды из строки MDI"""
        cmd = self.window.txt_mdi.text().strip()
        if cmd and self.conn_worker:
            self.write_to_log_file("[MDI -> ЧПУ]", cmd)
            self.conn_worker.send_command(cmd)
            self.window.txt_mdi.clear()

    def handle_telemetry_packet(self, status, x, y, z, is_homed, current_line):
        """Прослойка для логирования сырой телеметрии и пуша ее в CNCState"""
        # Логируем пакет телеметрии в файл для истории отладки
        raw_packet_str = f"<Status:{status}|Pos:X={x},Y={y},Z={z}|Hom:{int(is_homed)}|Line={current_line}>"
        self.write_to_log_file("[ЧПУ TELEM]", raw_packet_str)
        
        # Обновляем состояние
        self.state.update_telemetry(status, x, y, z, is_homed, current_line)

    def sync_gui_with_state(self):
        self.window.static_control.update_all_coordinates(
            self.state.x, self.state.y, self.state.z,
            self.state.m_x, self.state.m_y, self.state.m_z
        )

        # Передаем именно МАШИННЫЕ координаты (MCS), так как сетка станка привязана к физическому полю
        self.window.view_3d.update_tool_position(self.state.m_x, self.state.m_y, self.state.m_z)

        self.window.setWindowTitle(f"CNC Portal HMI [Статус: {self.state.status} | Кадр: {self.state.current_line}]")
        
        if self.state.is_homed:
            self.window.lbl_comp_status.setText(" MACHINE: HOMED ")
            self.window.lbl_comp_status.setStyleSheet("background-color: #00ff00; color: #000; font-weight: bold; font-size: 10px; margin-right: 4px;")
        else:
            self.window.lbl_comp_status.setText(" MACHINE: NOT HOMED ")
            self.window.lbl_comp_status.setStyleSheet("background-color: #aa0000; color: #fff; font-weight: bold; font-size: 10px; margin-right: 4px;")

    def on_window_close(self, event):
        if self.conn_worker:
            self.conn_worker.stop()
        event.accept()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec())

    def handle_open_settings(self):
        """Безопасное открытие окна конфигурации"""
        # Принудительно перерисовываем перед выводом
        self.settings_dialog.populate_table()
        # Открываем в режиме модального диалога
        self.settings_dialog.exec()


if __name__ == "__main__":
    cnc_app = CNCApplication()
    cnc_app.run()
