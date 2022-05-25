from threading import Thread, Event
from .serialio import Serial
from .buffer import Buffer


class OscilloscopeBase:
    def __init__(self, timeout: float = .5, emitAsDict: bool = False):
        self.serial = Serial(name="arduino", timeout=timeout, emitAsDict=emitAsDict)
        self.buffer = Buffer(maxlen=200)

    def start(self):
        self.serial.start()

    def stop(self):
        self.serial.stop()