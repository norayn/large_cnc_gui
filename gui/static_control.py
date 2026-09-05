# gui/static_control.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGridLayout

class StaticControlWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #262626; border-radius: 4px;")
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        
        # Сетка для DRO: 3 строки (X, Y, Z), 2 колонки (Колонка 1 - WCS, Колонка 2 - MCS)
        dro_grid = QGridLayout()
        dro_grid.setSpacing(2)
        dro_grid.setHorizontalSpacing(10) # Небольшой отступ между WCS и MCS
        
        # Метки для Рабочих координат (Крупные, Зеленые)
        self.lbl_x_wcs = QLabel("X: 0.000")
        self.lbl_y_wcs = QLabel("Y: 0.000")
        self.lbl_z_wcs = QLabel("Z: 0.000")
        for lbl in [self.lbl_x_wcs, self.lbl_y_wcs, self.lbl_z_wcs]:
            lbl.setStyleSheet("font-family: 'Consolas', monospace; font-size: 18px; color: #00ff00; font-weight: bold; background: transparent;")
            
        # Метки для Машинных координат (Поменьше, Серые, в скобках)
        self.lbl_x_mcs = QLabel("[M: 0.000]")
        self.lbl_y_mcs = QLabel("[M: 0.000]")
        self.lbl_z_mcs = QLabel("[M: 0.000]")
        for lbl in [self.lbl_x_mcs, self.lbl_y_mcs, self.lbl_z_mcs]:
            lbl.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px; color: #888888; background: transparent; padding-top: 6px;") 
            # padding-top сдвигает их чуть ниже, чтобы они красиво выравнивались по базовой линии крупных цифр
            
        # Раскладываем в сетку
        dro_grid.addWidget(self.lbl_x_wcs, 0, 0)
        dro_grid.addWidget(self.lbl_x_mcs, 0, 1)
        
        dro_grid.addWidget(self.lbl_y_wcs, 1, 0)
        dro_grid.addWidget(self.lbl_y_mcs, 1, 1)
        
        dro_grid.addWidget(self.lbl_z_wcs, 2, 0)
        dro_grid.addWidget(self.lbl_z_mcs, 2, 1)
        
        layout.addLayout(dro_grid)
        
        # Блок шпинделя и СОЖ (Остается без изменений)
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

    def update_all_coordinates(self, w_x, w_y, w_z, m_x, m_y, m_z):
        """Обновленный публичный метод API для одновременного вывода WCS и MCS"""
        self.lbl_x_wcs.setText(f"X: {w_x:.3f}")
        self.lbl_y_wcs.setText(f"Y: {w_y:.3f}")
        self.lbl_z_wcs.setText(f"Z: {w_z:.3f}")
        
        self.lbl_x_mcs.setText(f"[M: {m_x:.3f}]")
        self.lbl_y_mcs.setText(f"[M: {m_y:.3f}]")
        self.lbl_z_mcs.setText(f"[M: {m_z:.3f}]")
