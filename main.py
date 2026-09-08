import sys
from PySide6.QtWidgets import QApplication
from main_window import MainWindow

APP_STYLESHEET = """
QPushButton {
    min-height: 40px;
    min-width: 80px;
    font-size: 20px;
}
QLineEdit, QSpinBox, QComboBox {
    min-height: 40px;
    font-size: 20px;
}

QLabel {
    font-size: 20px;
}

QTabBar::tab {
    font-size: 20px;
    min-height: 40px;
    min-width: 80px;
}
"""

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.showFullScreen()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
