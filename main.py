# main.py
import sys
from PyQt6.QtWidgets import QApplication

# Импортируем готовое окно из нашего пакета gui
from gui.main_window import CNCMainWindow

def main():
    # Инициализация Qt-приложения
    app = QApplication(sys.argv)
    
    # Создание главного окна
    window = CNCMainWindow()
    window.show()
    
    # Запуск бесконечного цикла обработки событий Qt
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
