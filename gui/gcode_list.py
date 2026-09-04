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
        
        # Вместо addStretch ставим полноценный виджет списка для Candle-стиля
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #101010; color: #ccc; border: none; font-family: 'Consolas', monospace; font-size: 11px; }
            QListWidget::item:selected { background-color: #004488; color: white; }
        """)
        # Тестовое наполнение для проверки расширенной ширины
        self.list_widget.addItems([
            "G90", "G21", "G0 Z5.000", "M3 S12000", 
            "G1 X100.520 Y23.110 Z-1.000 F1200", 
            "G1 X120.000 Y25.400"
        ])
        layout.addWidget(self.list_widget)
