import pyqtgraph.opengl as gl

class CNCVisualizer3D(gl.GLViewWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: 1px solid #3a3a3a;")
        self.setCameraPosition(distance=2500, elevation=30, azimuth=-45)
        self.init_bed()
        
    def init_bed(self):
        # Отрисовка 4-метровой станины (4000 х 500 мм)
        grid = gl.GLGridItem()
        grid.setSize(4000, 500, 1)
        grid.setSpacing(100, 100, 0)
        self.addItem(grid)
