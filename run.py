import sys
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication


pathUI = os.path.dirname(os.path.abspath(__file__))
pathUI = os.path.join(pathUI, 'gui', 'main.ui')


class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(pathUI, self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Oscilloscope()
    w.show()
    sys.exit(app.exec_())
    