# gui/dialog_settings.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLabel, QHeaderView
from PyQt6.QtCore import pyqtSignal, Qt

class CNCSettingsDialog(QDialog):
    # Сигнал для отправки измененного конфига в главный файл -> станок
    config_change_requested = pyqtSignal(str)

    def __init__(self, state_obj, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Инженерные настройки контроллера ESP32")
        self.resize(550, 400)
        self.setMinimumSize(450, 300)
        
        self.machine_state = state_obj
        # Подписываемся на событие обновления конфигов, чтобы перерисовать таблицу при входящих данных по USB
        self.machine_state.config_updated.connect(self.populate_table)
        
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        
        lbl_info = QLabel("Дважды кликните по значению для изменения. После редактирования нажмите 'Сохранить'.")
        lbl_info.setStyleSheet("font-size: 10px; color: #888; font-weight: bold;")
        layout.addWidget(lbl_info)
        
        # Таблица параметров
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Параметр (Ключ)", "Текущее значение"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #151515; color: #ccc; gridline-color: #333; border: 1px solid #3a3a3a; font-family: monospace; font-size: 11px; }
            QHeaderView::section { background-color: #262626; color: #aaa; border: 1px solid #333; font-size: 11px; }
        """)
        layout.addWidget(self.table)
        
        # Нижняя панель кнопок
        bottom_layout = QHBoxLayout()
        
        btn_save = QPushButton("Сохранить изменения")
        btn_save.setStyleSheet("background-color: #005500; color: #fff; font-size: 11px; font-weight: bold; max-height: 24px; padding: 4px 12px;")
        btn_save.clicked.connect(self.save_edited_configs)
        
        btn_close = QPushButton("Закрыть")
        btn_close.setStyleSheet("background-color: #444; color: #fff; font-size: 11px; max-height: 24px;")
        btn_close.clicked.connect(self.accept)
        
        bottom_layout.addWidget(btn_save)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_close)
        layout.addLayout(bottom_layout)
        
        self.populate_table()

    def populate_table(self):
        """Заполнение таблицы данными из словаря состояния"""
        self.table.setRowCount(0)
        configs = self.machine_state.config
        
        self.table.setRowCount(len(configs))
        for row, (key, value) in enumerate(configs.items()):
            # Ячейка ключа (блокируем для редактирования)
            item_key = QTableWidgetItem(key)
            item_key.setFlags(item_key.flags() ^ Qt.ItemFlag.ItemIsEditable)
            item_key.setForeground(Qt.GlobalColor.darkGray)
            
            # Ячейка значения (можно редактировать)
            item_val = QTableWidgetItem(str(value))
            
            self.table.setItem(row, 0, item_key)
            self.table.setItem(row, 1, item_val)

    def save_edited_configs(self):
        """Построчный анализ изменений и отправка команд в формате SET_CONFIG:key=value"""
        configs_in_state = self.machine_state.config
        
        for row in range(self.table.rowCount()):
            key = self.table.item(row, 0).text()
            current_ui_value = self.table.item(row, 1).text().strip()
            
            # Сравниваем значение в таблице со значением, которое было в памяти
            if key in configs_in_state and configs_in_state[key] != current_ui_value:
                # Значение изменилось! Формируем команду по вашему ТЗ
                set_cmd = f"SET_CONFIG:{key}={current_ui_value}"
                
                # Обновляем локально в состоянии
                configs_in_state[key] = current_ui_value
                
                # Выстреливаем команду в станок
                self.config_change_requested.emit(set_cmd)
                
        self.populate_table() # Перерисовываем таблицу

    def showEvent(self, event):
        """Автоматический вызов при каждом открытии окна оператором"""
        super().showEvent(event)
        # Принудительно обновляем таблицу актуальными данными из состояния станка
        self.populate_table()
