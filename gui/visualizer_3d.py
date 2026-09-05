# gui/visualizer_3d.py
import numpy as np
import pyqtgraph.opengl as gl
from PyQt6.QtGui import QColor

class CNCVisualizer3D(gl.GLViewWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: 1px solid #3a3a3a;")
        
        # Настраиваем камеру так, чтобы было видно всю 4-метровую станину
        self.setCameraPosition(distance=2800, elevation=35, azimuth=-60)
        
        # Массив для хранения истории перемещений (след фрезы)
        self.history_points = []
        
        self.init_scene()
        
    def init_scene(self):
        # 1. Отрисовка 4-метровой станины (4000 х 500 мм)
        # Смещаем сетку, чтобы машинный ноль (0,0,0) был в углу, а не в центре экрана
        self.grid = gl.GLGridItem()
        self.grid.setSize(4000, 500, 1)
        self.grid.setSpacing(100, 100, 0)
        self.grid.translate(2000, 250, 0) # Сдвигаем центр сетки в координаты (2000, 250)
        self.addItem(self.grid)
        
        # 2. Отрисовка пройденного пути (След фрезы)
        # Делаем линию полупрозрачной желтой или бирюзовой
        self.path_line = gl.GLLinePlotItem(
            color=QColor(0, 255, 255, 180), 
            width=2, 
            mode='line_strip'
        )
        self.addItem(self.path_line)
        
        # 3. Маркер инструмента (Фреза)
        # Создаем цилиндр (тело фрезы)
        cylinder_mesh = gl.MeshData.cylinder(rows=10, cols=16, radius=[3, 3], length=40)
        self.tool_marker = gl.GLMeshItem(
            meshdata=cylinder_mesh,
            smooth=True,
            color=(1.0, 0.0, 0.0, 1.0), # Ярко-красный цвет
            drawEdges=False
        )
        # Переворачиваем цилиндр, чтобы он смотрел вниз по оси Z, и поднимаем основание
        self.tool_marker.rotate(180, 1, 0, 0) 
        self.addItem(self.tool_marker)

    def update_tool_position(self, m_x, m_y, m_z):
        """
        API метод для обновления положения фрезы на 3D сцене.
        Вызывается из главного окна при получении каждого пакета телеметрии.
        """
        # 1. Перемещаем маркер фрезы в актуальные машинные координаты (MCS)
        self.tool_marker.resetTransform()
        # Корректируем разворот по Z
        self.tool_marker.rotate(180, 1, 0, 0)
        # Смещаем в точку из телеметрии (в ЧПУ Z идет вверх-вниз)
        self.tool_marker.translate(m_x, m_y, m_z)
        
        # 2. Добавляем точку в историю для рисования следа
        new_point = [m_x, m_y, m_z]
        
        # Защита от дубликатов: добавляем точку, только если инструмент реально сдвинулся
        if not self.history_points or not np.allclose(self.history_points[-1], new_point, atol=0.01):
            self.history_points.append(new_point)
            
            # Ограничиваем историю (например, последние 5000 точек), чтобы не перегружать видеокарту
            if len(self.history_points) > 5000:
                self.history_points.pop(0)
                
            # Обновляем данные линии на 3D сцене
            pts_array = np.array(self.history_points, dtype=np.float32)
            self.path_line.setData(pos=pts_array)

    def clear_path_history(self):
        """Метод очистки следа (например, при запуске нового файла G-кода)"""
        self.history_points = []
        self.path_line.setData(pos=None)
