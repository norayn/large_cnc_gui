# gui/dialog_log.py
import os
import re
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QCheckBox
from PyQt6.QtCore import Qt

class CNCLogWindow(QDialog):
    def __init__(self, log_path="cnc_session.log", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Полный терминал обмена ЧПУ (Лог-файл)")
        self.resize(720, 500)
        self.setMinimumSize(500, 350)
        self.log_path = log_path
        
        # Хранилище для сравнения дубликатов телеметрии (всего 1 строка в памяти)
        self.last_raw_telemetry = "" 
        
        self.setStyleSheet("background-color: #0d0d0d; color: #00ff00;")
        self.init_ui()
        self.load_existing_log()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # --- ВЕРХНЯЯ ПАНЕЛЬ ФИЛЬТРОВ (Новые галочки) ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)
        
        self.chk_hide_all_telem = QCheckBox("Скрывать всю телеметрию полностью")
        self.chk_hide_dup_telem = QCheckBox("Скрывать дубликаты телеметрии (без учета времени)")
        
        for chk in [self.chk_hide_all_telem, self.chk_hide_dup_telem]:
            chk.setStyleSheet("font-size: 11px; color: #aaa; font-weight: bold;")
        
        # Связываем переключение галочек с перезагрузкой лога с диска
        self.chk_hide_all_telem.stateChanged.connect(self._handle_filter_change)
        self.chk_hide_dup_telem.stateChanged.connect(self._handle_filter_change)
        
        filter_layout.addWidget(self.chk_hide_all_telem)
        filter_layout.addWidget(self.chk_hide_dup_telem)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Текстовое поле терминала
        self.txt_terminal = QTextEdit()
        self.txt_terminal.setReadOnly(True)
        self.txt_terminal.setStyleSheet("""
            QTextEdit { 
                font-family: 'Consolas', monospace; 
                font-size: 11px; 
                border: 1px solid #333; 
                background-color: #050505;
            }
        """)
        layout.addWidget(self.txt_terminal)
        
        # Нижняя панель управления окном
        bottom_layout = QHBoxLayout()
        
        btn_clear = QPushButton("Очистить файл лога")
        btn_clear.setStyleSheet("background-color: #331111; color: #ff5555; font-size: 11px; max-height: 22px; font-weight: bold;")
        btn_clear.clicked.connect(self.clear_log_file)
        
        btn_close = QPushButton("Закрыть")
        btn_close.setStyleSheet("background-color: #333; color: #fff; font-size: 11px; max-height: 22px;")
        btn_close.clicked.connect(self.hide)
        
        bottom_layout.addWidget(btn_clear)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_close)
        layout.addLayout(bottom_layout)

    def load_existing_log(self):
        """Считывание накопленного лога с диска с применением выбранных фильтров"""
        self.txt_terminal.clear()
        self.last_raw_telemetry = "" # Сброс при перезагрузке файла
        
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    # Читаем лог с конца, берем последние 1000 строк для анализа
                    all_lines = f.readlines()[-1000:]
                    
                    filtered_lines = []
                    for line in all_lines:
                        should_show, clean_telem = self._process_filter_logic(line.strip())
                        if should_show:
                            filtered_lines.append(line.strip())
                            if clean_telem:
                                self.last_raw_telemetry = clean_telem
                                
                    self.txt_terminal.setPlainText("\n".join(filtered_lines))
                    self._scroll_to_bottom()
            except Exception:
                self.txt_terminal.append("--- Ошибка чтения файла лога ---")

    def append_log_line(self, line):
        """Слот для динамического вывода новой входящей строки в реальном времени"""
        if self.isVisible():
            should_show, clean_telem = self._process_filter_logic(line)
            if should_show:
                self.txt_terminal.append(line)
                self._scroll_to_bottom()
                
            # Важно обновлять состояние последнего пакета, даже если окно скрыто,
            # чтобы при открытии окна фильтр дубликатов работал корректно
            if clean_telem:
                self.last_raw_telemetry = clean_telem

    def _process_filter_logic(self, line):
        """
        Внутренний инжиниринг фильтрации.
        Возвращает: (bool: показывать ли строку, str: очищенный пакет телеметрии или None)
        """
        # Проверяем, является ли строка пакетом телеметрии [ЧПУ TELEM] <Status:...>
        if "[ЧПУ TELEM]" in line:
            # 1. Если включена галочка "Скрыть всю телеметрию" — сразу отсекаем
            if self.chk_hide_all_telem.isChecked():
                return False, None
                
            # 2. Если включена галочка "Скрывать дубликаты"
            if self.chk_hide_dup_telem.isChecked():
                # Вытаскиваем сам блок данных <Status:...> с помощью регулярного выражения,
                # полностью отбрасывая временную метку лога [14:45:13.002]
                match = re.search(r"(<Status:.*>)", line)
                if match:
                    current_telem = match.group(1)
                    
                    # Сравниваем тело пакета с предыдущим сохраненным
                    if current_telem == self.last_raw_telemetry:
                        return False, current_telem # Строка совпадает, скрываем дубликат
                    else:
                        return True, current_telem # Строка изменилась (например, поменялась координата), показываем
                        
                return True, None
                
            # Если галочки не активны, но это телеметрия — возвращаем ее чистое тело для обновления кэша
            match = re.search(r"(<Status:.*>)", line)
            return True, match.group(1) if match else None
            
        # Все остальные строки (GUI команды, MDI, ответы ok) пропускаем всегда
        return True, None

    def _handle_filter_change(self, state):
        """Логика взаимной блокировки галочек и обновления экрана"""
        sender = self.sender()
        
        # Если оператор выбрал "Скрывать ВСЁ", то галочка "Скрывать только дубликаты" теряет смысл
        if sender == self.chk_hide_all_telem and self.chk_hide_all_telem.isChecked():
            self.chk_hide_dup_telem.setChecked(False)
            self.chk_hide_dup_telem.setEnabled(False)
        elif sender == self.chk_hide_all_telem and not self.chk_hide_all_telem.isChecked():
            self.chk_hide_dup_telem.setEnabled(True)
            
        # Перечитываем файл с диска и перерисовываем окно под новые правила
        self.load_existing_log()

    def clear_log_file(self):
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write("--- Лог очищен оператором ---\n")
            self.txt_terminal.setPlainText("--- Лог очищен оператором ---\n")
            self.last_raw_telemetry = ""
        except Exception:
            pass

    def _scroll_to_bottom(self):
        v_bar = self.txt_terminal.verticalScrollBar()
        v_bar.setValue(v_bar.maximum())
