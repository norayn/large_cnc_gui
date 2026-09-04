from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton

class StaticControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #262626; border-radius: 4px;")
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        
        # DRO Координаты
        dro_layout = QVBoxLayout()
        dro_layout.setSpacing(2)
        self.lbl_x = QLabel("X: 0.000")
        self.lbl_y = QLabel("Y: 0.000")
        self.lbl_z = QLabel("Z: 0.000")
        for lbl in [self.lbl_x, self.lbl_y, self.lbl_z]:
            lbl.setStyleSheet("font-family: 'Consolas', monospace; font-size: 18px; color: #00ff00; font-weight: bold;")
        dro_layout.addWidget(self.lbl_x)
        dro_layout.addWidget(self.lbl_y)
        dro_layout.addWidget(self.lbl_z)
        layout.addLayout(dro_layout)
        
        # Шпиндель / СОЖ
        spindle_layout = QVBoxLayout()
        spindle_layout.setSpacing(3)
        lbl_title = QLabel("ШПИНДЕЛЬ / СОЖ")
        lbl_title.setStyleSheet("font-size: 10px; color: #888; font-weight: bold;")
        
        self.btn_spindle = QPushButton("ШПИНДЕЛЬ [ВЫКЛ]")
        self.btn_coolant = QPushButton("ОХЛАЖДЕНИЕ [ВЫКЛ]")
        for btn in [self.btn_spindle, self.btn_coolant]:
            btn.setStyleSheet("background-color: #3a3a3a; font-size: 10px; padding: 3px; max-height: 22px;")
            
        spindle_layout.addWidget(lbl_title)
        spindle_layout.addWidget(self.btn_spindle)
        spindle_layout.addWidget(self.btn_coolant)
        layout.addLayout(spindle_layout)

    def update_coordinates(self, x, y, z):
        """Публичный метод (API) для обновления DRO из главного окна"""
        self.lbl_x.setText(f"X: {x:.3f}")
        self.lbl_y.setText(f"Y: {y:.3f}")
        self.lbl_z.setText(f"Z: {z:.3f}")
