from socket import timeout
import sys
import signal
import os
from oscilloscope.base import OscilloscopeBase
from oscilloscope.utils import dbScale
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
import numpy as np
from threading import Thread
import json


pathUI = os.path.dirname(os.path.abspath(__file__))
pathUI = os.path.join(pathUI, 'gui', 'main.ui')


PEN_COLOR = (0, 190, 255)


class Oscilloscope(QMainWindow, OscilloscopeBase):
    def __init__(self):
        super().__init__()
        uic.loadUi(pathUI, self)
        self.__configureGraph()
        self.__configureSerial()
        # self.__configureBuffer()
        self.__configureButtons()

    def __configureGraph(self):
        """Configures the signal graph."""
        self.graph.showGrid(x=True, y=True)
        self.graph.setYRange(0, 1024)
        self.curve = self.graph.plot(pen=PEN_COLOR)
        self.winSize.valueChanged.connect(lambda value: self.buffer.setNewLen(value))
        t = np.linspace(0, 2, 1000)
        x = np.sin(2 * np.pi * t) + 3 * np.cos(2 * np.pi * 3 * t)
        self.curve.setData(t, x)

    def __configureButtons(self):
        """Configures the GUI buttons."""
        self.connectBtn.clicked.connect(self.updatePortDevice)

    def __configureSerial(self):
        """Configures the serial device variables."""
        self.baudrates.addItems(['1200', '2400', '4800', '9600', '14400', '19200', '28800', '31250', '57600', '115200'])
        self.baudrates.setCurrentIndex(3)
        self.updateListOfPorts(self.serial.ports())
        self.serial.on('connection', self.updateSerialConnectionStatus)
        self.serial.on('ports', self.updateListOfPorts)
        self.serial.on('data', lambda data: print('received: ', data))

    def updateSerialConnectionStatus(self, status):
        """Updates the connection status on the GUI."""
        self.connectBtn.setChecked(status)

    def updateListOfPorts(self, ports):
        """Updates the list of port on the GUI."""
        self.devices.clear()
        self.devices.addItems(ports)

    def updateBuffer(self, data):
        self.buffer.append(data)

    def updatePortDevice(self):
        """Updates a new value for the port device."""
        device = self.devices.currentText()
        self.connectBtn.setChecked(False)
        if not self.serial.isOpen():
            self.serial.port = device
        else:
            self.serial.disconnect(force=True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Oscilloscope()
    w.show()
    w.start()
    sys.exit(app.exec_())
