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

        # СВЯЗЫВАНИЕ ПЕРЕМЕННЫХ И СОСТОЯНИЯ ДЛЯ ВКЛАДОК
        self.window.control_tabs.tab_jog.set_state_reference(self.state)
        self.window.control_tabs.tab_files.set_state_reference(self.state) # Передаем state во вкладку файлов
        
        # Подписываем ленту на экране на сигнал ручной генерации тест-квадрата
        self.window.control_tabs.tab_files.gcode_loaded_notify.connect(self.handle_gcode_loaded_ui)
        
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
        """Перехват всех текстовых ответов, эхо-команд и логов от ESP32"""
        # 1. Записываем строку в сессионный лог на диск ноутбука
        self.write_to_log_file("[ЧПУ -> GUI]", msg)
        
        # 2. ИНТЕЛЛЕКТУАЛЬНЫЙ ПЕРЕХВАТ КОНФИГУРАЦИИ
        # Если пришедшая строка — это наши параметры конфигурации, отдаем их в модель состояния
        if "CONFIG_DATA:" in msg:
            # На случай, если строка пришла с префиксом диагностики [DEBUG RAW INCOMING], 
            # очищаем её, оставляя только чистое тело данных
            clean_config = msg if msg.startswith("CONFIG_DATA:") else msg.split(">>>")[-1].split("<<<")[0]
            
            if clean_config.startswith("CONFIG_DATA:"):
                # Скармливаем строку парсеру словаря в machine_state.py
                self.state.parse_config_string(clean_config)
                
                # Подсвечиваем нижнюю полоску лога голубым цветом успеха
                self.window.lbl_log_preview.setStyleSheet("font-size: 11px; color: #00ffff; font-weight: bold;")
                self.window.lbl_log_preview.setText("ЛОГ: Конфигурация успешно импортирована в память GUI!")
                return # Выходим из метода, чтобы не затирать надпись лога ниже
                
        # 3. Обработка всех остальных штатных ответов (ok, error и т.д.)
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
        """Реактивный обработчик пакетов телеметрии от ESP32"""
        # Гарантируем, что номер кадра — это строго целое число (int)
        line_index = int(current_line)
        
        # Формируем красивую отладочную строчку для потоковой записи на диск cnc_session.log
        # Теперь здесь гарантированно будет выводиться число (Line=0, Line=1, Line=5 и т.д.)
        raw_packet_str = f"<Status:{status}|Pos:X={x:.2f},Y={y:.2f},Z={z:.2f}|Hom:{1 if is_homed else 0}|Line={line_index}>"
        self.write_to_log_file("[ЧПУ TELEM]", raw_packet_str)
        
        # Пушим данные в Единый Источник Истины (CNCMachineState)
        self.state.update_telemetry(status, x, y, z, is_homed, line_index)

    def handle_gcode_loaded_ui(self):
        """Слот: переносит сгенерированные строки из памяти состояния на экран ноутбука"""
        self.window.gcode_zone.load_lines(self.state.gcode_lines)
        self.window.lbl_log_preview.setText("ЛОГ: Сгенерирована тестовая программа обхода квадрата 200х200 мм.")

    def sync_gui_with_state(self):
        self.window.static_control.update_all_coordinates(
            self.state.x, self.state.y, self.state.z,
            self.state.m_x, self.state.m_y, self.state.m_z
        )

        # Передаем именно МАШИННЫЕ координаты (MCS), так как сетка станка привязана к физическому полю
        self.window.view_3d.update_tool_position(self.state.m_x, self.state.m_y, self.state.m_z)

        self.window.setWindowTitle(f"CNC Portal HMI [Статус: {self.state.status} | Кадр: {self.state.current_line}]")

        self.window.gcode_zone.highlight_line(self.state.current_line)
        
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
