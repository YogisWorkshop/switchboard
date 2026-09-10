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
QSpinBox::up-button, QSpinBox::down-button {
    width: 40px;
    height: 20px;
}
QScrollBar:vertical {
    width: 30px;
}
QScrollBar::handle:vertical {
    background: #999999;
    min-height: 40px;
    border-radius: 6px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
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
