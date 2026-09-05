# gui/control_tabs.py
from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtCore import pyqtSignal

# Импортируем изолированные виджеты вкладок из подпапки gui/tabs
from gui.tabs.tab_jog import TabJogWidget
from gui.tabs.tab_files import TabFilesWidget
from gui.tabs.tab_align import TabAlignWidget
from gui.tabs.tab_diag import TabDiagWidget

class ControlTabsWidget(QTabWidget):
    # Единый выходной канал команд для главного окна
    command_requested = pyqtSignal(str)
    # Сигнал для открытия поп-апа с графиками
    open_charts_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTabWidget::panel { border: 1px solid #3a3a3a; background-color: #222; }
            QTabBar::tab { background: #333; color: #aaa; padding: 4px 10px; font-size: 11px; }
            QTabBar::tab:selected { background: #222; color: #fff; font-weight: bold; }
        """)
        self.init_ui()
        
    def init_ui(self):
        # Инициализируем объекты вкладок
        self.tab_jog = TabJogWidget()
        self.tab_files = TabFilesWidget()
        self.tab_align = TabAlignWidget()
        self.tab_diag = TabDiagWidget()
        
        # Добавляем их в контейнер табов
        self.addTab(self.tab_jog, "Ручной JOG")
        self.addTab(self.tab_files, "G-Код Файлы")
        self.addTab(self.tab_align, "Выравнивание")
        self.addTab(self.tab_diag, "Диагностика")
        
        # --- СВЯЗЫВАНИЕ СИГНАЛОВ (МАРШРУТИЗАЦИЯ) ---
        # Любой внутренний запрос команды перенаправляется на единый выходной сигнал
        self.tab_jog.command_requested.connect(self.command_requested.emit)
        self.tab_files.command_requested.connect(self.command_requested.emit)
        self.tab_align.command_requested.connect(self.command_requested.emit)
        self.tab_diag.command_requested.connect(self.command_requested.emit)
        
        # Пробрасываем клик по кнопке вызова окна графиков
        self.tab_diag.charts_clicked.connect(self.open_charts_requested.emit)
