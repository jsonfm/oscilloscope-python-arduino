from serial import Serial
from serial.tools import list_ports
from threading import Thread, Event
import time
from .sevent import Emitter


class CustomSerial(Emitter):
    """A custom serial class threaded and event emit based.

    :param reconnectDelay: wait time between reconnection attempts
    :param maxAttempts: max read attempts.
    """
    def __init__(self, reconnectDelay=1, maxAttempts=10, refreshTime=1, *args, **kwargs):
        super().__init__()
        self.serial = Serial(*args, **kwargs)
        self.thread = Thread(target=self.run)
        self.runningEvent = Event()
        self.reconnectDelay = reconnectDelay
        self.lastConnectionState = False
        self.maxAttempts = maxAttempts
        self.attempts = 0
        self.refreshTime = refreshTime
        self.time = 0
        self.lastDevicesList = []
    
    def __setitem__(self, key, value):
        if self.serial.isOpen():
            self.serial.close()
        setattr(self.serial, key, value)
    
    def hasDevice(self):
        return self.serial.port is not None

    def isOpen(self):
        """It checks if serial port device is open."""
        return self.serial.isOpen()

    def attemptsLimitReached(self):
        """Check if read attempts have reached their limit."""
        return self.attempts >= self.maxAttempts

    def start(self):
        """It starts read loop."""
        self.runningEvent.set()
        self.thread.start()

    def getListOfPorts(self):
        """It returns a list with the availables serial port devices."""
        ports = [port.device for port in list_ports.comports()]
        return ports

    def connect(self):
        """It will try to connect with the specified serial device."""
        try:
            self.lastConnectionState = self.serial.isOpen()
            if self.serial.isOpen():
                self.serial.close()
            self.serial.open()
        except Exception as e:
            print('connection error: ',e)

    def write(self, message:str):
        """It writes a message to the serial device.

        :param message: string to be sent.
        """
        if self.serial.isOpen():
            try:
                message = message.encode()
                self.serial.write(message)
            except Exception as e:
                print('Write error: ', e)

    def readData(self):
        """It will try to read incoming data."""
        try:
            data = self.serial.readline().decode().rstrip()
            if len(data) > 0:
                return data
        except Exception as e:
            print('Read data error: ', e)
            if not self.attemptsLimitReached():
                self.attempts += 1
            else:
                self.attempts = 0
                try:
                    self.serial.close()
                except Exception as e:
                    print(e)
            return None

    def run(self):
        """Here the run loop is executed."""
        while self.runningEvent.is_set():
            # Check if there was a change on the connection status
            t0 = time.time()

            if self.lastConnectionState != self.serial.isOpen():
                self.emit('connection-status', self.serial.isOpen())
                self.lastConnectionState = self.serial.isOpen()

            if self.serial.isOpen():
                data = self.readData()
                if data is not None:
                    self.emit('data-incoming', data)
            else:
                if self.hasDevice():
                    self.connect()
                time.sleep(self.reconnectDelay)
            
            t1 = time.time()
            dt = t1 - t0
            self.time += dt

            if self.time >= self.refreshTime:
                self.time = 0
                actualDevicesList = self.getListOfPorts()
                if actualDevicesList != self.lastDevicesList:
                    self.lastDevicesList = actualDevicesList
                    self.emit('ports-update',  actualDevicesList)

    def disconnect(self):
        if self.serial.port is not None:
            self.serial.close()
            self.serial.port = None

    def stop(self):
        """It stops the read loop an closed the connection with the serial device."""
        self.runningEvent.clear()
        self.serial.close()

# serial = CustomSerial(timeout=0.5, baudrate=9600)
# ports = serial.getListOfPorts()
# serial['port'] = ports[-1]

# signal.signal(signal.SIGINT, lambda signum, handler: serial.stop())

# serial.on('data-incoming', lambda data: print('Received data: ', data))
# serial.on('connection-status', lambda state: print('Serial Connection Status: ', state))
# serial.start()


