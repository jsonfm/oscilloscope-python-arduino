import sys
import signal
import os
from oscilloscope.customSerial import CustomSerial
from oscilloscope.buffer import MultipleBuffers
from oscilloscope.utils import dbScale
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
import numpy as np
import json


pathUI = os.path.dirname(os.path.abspath(__file__))
pathUI = os.path.join(pathUI, 'gui', 'main.ui')


class Oscilloscope(QMainWindow):
    bufferIsFull = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(pathUI, self)

        self.__configureGraph()
        self.__configureBuffer()
        self.__configureButtons()
        self.__configureSerial()
        self.__configureMenuBar()

    def __configureGraph(self):
        self.graph.showGrid(x=True, y=True)
        self.curve = self.graph.plot(pen=(0,190,255))
        self.winSize.valueChanged.connect(lambda value: self.buffer.setNewLen(value))
        # self.clearBtn.clicked.connect(self.clearPlot)

    def __configureBuffer(self):
        self.buffer = MultipleBuffers(variables=['x'], autoclear=False, maxlen=100)
        self.buffer['x'].on('is-full', lambda: self.bufferIsFull.emit())
        self.bufferIsFull.connect(lambda: self.plot(self.buffer['x'].getData(), clear=True))

    def __configureButtons(self):
        self.connectBtn.clicked.connect(self.choosePortDevice)

    def __configureSerial(self):
        self.baudrates.addItems(['1200', '2400', '4800', '9600', '14400', '19200', '28800', '31250', '57600', '115200'])
        self.baudrates.setCurrentIndex(3)
        self.baudrates.currentTextChanged.connect(self.updateBaudrate)

        self.serial = CustomSerial(baudrate=9600)
        self.updatePortsList(self.serial.getListOfPorts())
        self.serial.on('connection-status', self.updateSerialConnectionStatus)
        self.serial.on('data-incoming', self.receiveNewData)
        self.serial.on('ports-update', self.updatePortsList)
        self.serial.start()

    def __configureMenuBar(self):
        self.actionOpen.triggered.connect(self.openFile)

    def choosePortDevice(self):
        device = self.devices.currentText()
        self.connectBtn.setChecked(False)
        if not self.serial.isOpen():
            self.serial['port'] = device
        else:
            self.serial.disconnect()

    def plot(self, *args,**kwargs):
        try:
            self.curve.setData(*args,**kwargs)
            if 'clear' in kwargs:
                clear = kwargs['clear']
                if clear:
                    self.buffer.clearAll()
        except Exception as e:
            print('Plot error: ', e)

    def clearPlot(self):
        self.curve.clear()

    def updateSerialConnectionStatus(self, status):
        self.connectBtn.setChecked(status)

    def updateBaudrate(self, baudrate):
        self.serial['baudrate'] = baudrate

    def updatePortsList(self, ports:list):
        self.devices.clear()
        self.devices.addItems(ports)
    
    def updateChannelsList(self, channels:list):
        self.channels.clear()
        self.channels.addItems(channels)

    def receiveNewData(self, data):
        try:
            variables = json.loads(data)
            self.buffer.appendAll(variables)
        except Exception as e:
            print(e)

    def updateChannelPlot(self, name=None):
        if name is None:
            variable = self.channels.currentText()
        else:
            variable = name
        if len(variable) > 0:
            self.plot(self.buffer[variable].getData(), clear=False)

    def openFile(self):
        dlg = QFileDialog()
        filesFilter = "CSV(*.csv);; All files(*.*)"
        filepath = dlg.getOpenFileName(self, "Choose a directory", "", filesFilter)[0]
        print('filepath: ', filepath)
        if len(filepath) > 0:
            self.buffer.load(filepath)
            if len(self.buffer) > 0:
                self.updateChannelsList(self.buffer.keys())
                self.updateChannelPlot()
                    
    def stop(self):
        self.serial.stop()
        self.buffer.clearAll()

    def closeEvent(self, event):
        self.stop()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Oscilloscope()
    signal.signal(signal.SIGINT, lambda signum, handler: w.closeEvent(None))
    w.show()
    sys.exit(app.exec_())
