import sys
import os
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from oscilloscope.serialio import Serial
from oscilloscope.buffer import Buffer
from oscilloscope.utils import dbScale, SamplerTimeCounter, TimerCount


pathUI = os.path.dirname(os.path.abspath(__file__))
pathUI = os.path.join(pathUI, 'gui', 'main.ui')


PEN_COLOR = (0, 190, 255)
FPS = 15


class Oscilloscope(QMainWindow):
    """An oscilloscope app."""
    def __init__(self):
        super().__init__()
        uic.loadUi(pathUI, self)
        self.__configureGraph()
        self.__configureSerial()
        self.__configureBuffer()
        self.__configureButtons()
        self.__configureTimers()

    def __configureBuffer(self):
        """Configures the buffer."""
        self.buffer = Buffer(maxlen=200)

    def __configureGraph(self):
        """Configures the signal graph."""
        self.graph.showGrid(x=True, y=True)
        self.graph.setYRange(0, 5)
        self.curve = self.graph.plot(pen=PEN_COLOR)
        self.winSize.valueChanged.connect(lambda value: self.buffer.setNewLen(value))
        self.graphTimer = QTimer()
        self.graphTimer.timeout.connect(self.updateGraph)
        self.graphTimer.start(1000 // FPS) # 1000 // FPS

    def __configureButtons(self):
        """Configures the GUI buttons."""
        self.connectBtn.clicked.connect(self.updatePortDevice)

    def __configureSerial(self):
        """Configures the serial device variables."""
        self.baudrates.addItems(['1200', '2400', '4800', '9600', '14400', '19200', '28800', '31250', '57600', '115200'])
        self.baudrates.setCurrentIndex(3)
        self.serial = Serial(name="arduino", timeout=.5, emitAsDict=False)
        self.serial.on('connection', self.updateSerialConnectionStatus)
        self.serial.on('ports', self.updateListOfPorts)
        self.serial.on('data', self.updateBuffer)
        self.updateListOfPorts(self.serial.ports())

    def __configureTimers(self):
        """Configures timers."""
        self.samplerTimerCounter = SamplerTimeCounter()
        self.frequencyLabelTimer = TimerCount(
            interval=1, 
            callback = lambda: self.fsLabel.setText(f"{self.samplerTimerCounter.lastFrequency():.5f}")
        )

    def updateSerialConnectionStatus(self, status: bool):
        """Updates the connection status on the GUI."""
        self.connectBtn.setChecked(status)

    def updateListOfPorts(self, ports: list = []):
        """Updates the list of port on the GUI."""
        self.devices.clear()
        self.devices.addItems(ports)

    def updateBuffer(self, data: str):
        """Updates signal buffer values."""
        self.buffer.append(float(data))
        self.frequencyLabelTimer.update()
        self.samplerTimerCounter.update()

    def updateGraph(self):   
        """Plots the signal over the corresponding GUI element."""    
        data = self.buffer.getData()
        self.curve.setData(data)

        # When the buffer is full clear it
        if self.buffer.isFull():
            self.buffer.clear()
        
    def updatePortDevice(self):
        """Updates a new value for the port device."""
        device = self.devices.currentText()
        self.connectBtn.setChecked(False)
        if not self.serial.isOpen():
            self.serial.port = device
        else:
            self.serial.disconnect(force=True)
    
    def start(self):
        """Starts the serial read loop."""
        self.serial.start()

    def close(self, event):
        """Stops serial thread."""
        self.serial.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Oscilloscope()
    w.show()
    w.start() # 
    sys.exit(app.exec_())
