# gui/gcode_list.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget

class GCodeListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #151515; border: 1px solid #3a3a3a;")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        lbl_title = QLabel("ЛЕНТА G-КОДА")
        lbl_title.setStyleSheet("font-size: 10px; color: #666; font-weight: bold; font-family: sans-serif;")
        layout.addWidget(lbl_title)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #101010; color: #ccc; border: none; font-family: 'Consolas', monospace; font-size: 11px; }
            QListWidget::item:selected { background-color: #004488; color: white; font-weight: bold; }
        """)
        layout.addWidget(self.list_widget)

    def load_lines(self, lines_list):
        """Метод полной перезагрузки списка строк на экране"""
        self.list_widget.clear()
        self.list_widget.addItems(lines_list)

    def highlight_line(self, line_num):
        """Слот подсветки текущего кадра (вызывается реактивно при смене кадра в телеметрии)"""
        if 0 <= line_num < self.list_widget.count():
            self.list_widget.setCurrentRow(line_num)
            # Автоматический скроллинг ленты, чтобы текущий кадр всегда был по центру экрана ноутбука
            item = self.list_widget.item(line_num)
            self.list_widget.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)
