"""
===============================================
remio library source-code is deployed under the Apache 2.0 License:
Copyright (c) 2022 Jason Francisco Macas Mora(@Hikki12) <franciscomacas3@gmail.com>
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
   http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
===============================================
"""

# System modules
from typing import Union
from threading import Thread, Event
import time
import json

# Third-party modules
from serial import Serial as PySerial
from serial.tools import list_ports

# Custom modules
from .sevent import Emitter


class Serial(Emitter):
    """A custom serial class threaded and event emit based.
    Args:
        name: device name.
        reconnectDelay: wait time between reconnection attempts.
        maxAttempts: max read attempts.
        portsRefreshTime: time for check serial devices changes (secs).
        emitterIsEnabled: disable on/emit events (callbacks execution).
        emitAsDict: emit events on dict format {'emitter_name': data} ?
    Events:
        data: it's emitted when new data is available.
        connection: it's emitted when the connection status is updated.
        ports: it's emitted when a new device is found or disconnected.
    """

    def __init__(
        self,
        name: str = "default",
        reconnectDelay: Union[int, float] = 1,
        maxAttempts: int = 10,
        portsRefreshTime: int = 1,
        emitterIsEnabled: bool = True,
        emitAsDict: bool = True,
        *args,
        **kwargs,
    ):
        super().__init__(emitterIsEnabled=emitterIsEnabled, *args, **kwargs)
        self.name = name
        self.port = kwargs.pop("port", None)
        self.reconnectDelay = reconnectDelay
        self.maxAttempts = maxAttempts
        self.portsRefreshTime = portsRefreshTime
        self.emitAsDict = emitAsDict
        self.lastConnectionState = False
        self.attempts = 0
        self.time = 0
        self.lastDevicesList = []
        self.serial = PySerial(*args, **kwargs)

        self.thread = Thread(target=self.run, name="serial-thread", daemon=True)
        self.running = Event()
        self.pauseEvent = Event()
        self.resume()

    def __setitem__(self, key, value):
        if self.serial.isOpen():
            self.serial.close()
        setattr(self.serial, key, value)

    def isConnected(self):
        """Checks if the serial port is open."""
        return self.serial.isOpen()

    def getPort(self):
        """Ceturns the current port device."""
        return self.serial.port

    def setPort(self, port: str = None):
        """Updates the port device value."""
        if port is not None:
            self.serial.close()
            self.serial.port = port
            self.connect()

    def restorePort(self):
        """Restores the default serial port."""
        self.setPort(self.port)

    def resume(self):
        """Resumes the read loop."""
        self.pauseEvent.set()

    def pause(self):
        """Pauses the read loop."""
        self.pauseEvent.clear()

    def setPause(self, value: bool = True):
        """Updates the pause/resume state."""
        if value:
            self.pause()
        else:
            self.resume()

    def needAPause(self):
        """Pauses or resume the read loop."""
        self.pauseEvent.wait()

    def hasDevice(self):
        """Checks if a serial device is setted."""
        return self.port is not None

    def isOpen(self):
        """Checks if serial port device is open."""
        return self.serial.isOpen()

    def attemptsLimitReached(self):
        """Checks if read attempts have reached their limit."""
        return self.attempts >= self.maxAttempts

    def start(self):
        """Starts read loop."""
        self.running.set()
        self.thread.start()

    @staticmethod
    def ports():
        """Returns a list with the availables serial port devices."""
        return [port.device for port in list_ports.comports()]

    def connect(self):
        """Will try to connect with the specified serial device."""
        try:
            self.lastConnectionState = self.serial.isOpen()

            if self.serial.isOpen():
                self.serial.close()

            if self.serial.port is None and self.port is not None:
                self.serial.port = self.port

            self.serial.open()

        except Exception as e:
            print(f"-> Serial - {self.name} :: {e}")

    def dictToJson(self, message: dict = {}) -> str:
        """Converts a dictionary to a json str."""
        try:
            return json.dumps(message)
        except Exception as e:
            print(f"-> Serial - {self.name} :: {e}")
        return message

    def write(
        self, message: Union[str, dict] = "", end: str = "\n", asJson: bool = False
    ):
        """Writes a message to the serial device.
        Args:
            message: string to be sent.
            end: newline character to be concated with the message.
            asJson: convert to JSON?
        """
        if self.serial.isOpen():
            try:
                if len(message) > 0:
                    if asJson:
                        message = self.dictToJson(message)
                    message += end
                    message = message.encode()
                    self.serial.write(message)
            except Exception as e:
                print(f"-> Serial - {self.name} :: {e}")

    def readData(self):
        """Will try to read incoming data."""
        try:
            data = self.serial.readline().decode().rstrip()
            if len(data) > 0:
                if self.emitAsDict:
                    data = {self.name: data}
                self.emit("data", data)
                return data
        except Exception as e:
            print(f"-> Serial - {self.name} :: {e}")
            if not self.attemptsLimitReached():
                self.attempts += 1
            else:
                self.attempts = 0
                try:
                    self.serial.close()
                except Exception as e:
                    print(f"-> Serial - {self.name} :: {e}")
            return None

    def checkSerialPorts(self, dt: Union[int, float]):
        """Monitors if there are changes in the serial devices."""
        if self.portsRefreshTime > 0:
            self.time += dt
            if self.time >= self.portsRefreshTime:
                actualDevicesList = self.ports()
                if actualDevicesList != self.lastDevicesList:
                    self.lastDevicesList = actualDevicesList
                    self.emit("ports", actualDevicesList)
                self.time = 0

    def checkConnectionStatus(self):
        """Checks if the connection status changes."""
        if self.lastConnectionState != self.serial.isOpen():
            status = self.serial.isOpen()
            if self.emitAsDict:
                status = {self.name: status}
            self.emit("connection", status)
            self.lastConnectionState = self.serial.isOpen()

    def reconnect(self):
        """Tries to reconnect with the serial device."""
        if self.hasDevice():
            self.connect()
            time.sleep(self.reconnectDelay)

    def run(self):
        """Here the run loop is executed."""
        while self.running.is_set():
            t0 = time.time()

            self.checkConnectionStatus()

            if self.serial.isOpen():
                self.readData()
            else:
                self.reconnect()

            t1 = time.time()
            dt = t1 - t0

            self.checkSerialPorts(dt)
            self.needAPause()

    def disconnect(self, force: bool = False):
        """Clears the current serial port device.
        Args:
            force: force disconnection? prevents reconnection.
        """
        if self.serial.port is not None:
            self.serial.close()
            self.serial.port = None
            if force:
                self.port = None

    def stop(self):
        """Stops the read loop an closed the connection with the serial device."""
        self.resume()
        self.disconnect()
        if self.running.is_set():
            self.running.clear()
            self.thread.join()


class Serials:
    """A class for manage multiple serial devices at the same time.
    Args:
        name: device name.
        reconnectDelay: wait time between reconnection attempts.
        maxAttempts: max read attempts.
        portsRefreshTime: time for check serial devices changes.
        emitterIsEnabled: disable on/emit events (callbacks execution).
    Events:
        data: it's emitted when new data is available.
        connection: it's emitted when the connection status is updated.
        ports: it's emitted when a new device is found or disconnected.
    """

    def __init__(self, devices: dict = {}, *args, **kwargs):
        self.devices = {}
        if len(devices) > 0:
            for name, settings in devices.items():
                if isinstance(settings, dict):
                    self.devices[name] = Serial(name=name, **settings)

    def __len__(self):
        return len(self.devices)

    def __getitem__(self, key):
        if key in self.devices:
            return self.devices[key]

    def hasDevices(self):
        """Checks if there is some serial device on list."""
        return len(self.devices) > 0

    def setDevices(self, devices: list = [], *args, **kwargs):
        """Updates the current serial devices list.
        Args:
            devices: serial devices list.
        """
        if self.hasDevices():
            self.stopAll()
        devices = list(set(devices))
        self.devices = [Serial(port=name, *args, **kwargs) for name in devices]

    def startAll(self):
        """Starts all serial devices"""
        for device in self.devices.values():
            device.start()

    def startOnly(self, name: str = "default"):
        """Starts only one specific serial device.
        Args:
            name: device name.
        """
        if name in self.devices:
            self.devices[name].start()

    def stopAll(self):
        """Stops all serial devices running."""
        for device in self.devices.values():
            device.stop()

    def stopOnly(self, name: str = "default"):
        """Stops only one specific serial device.
        Args:
            name: device name.
        """
        if name in self.devices:
            self.device[name].stop()

    def pauseOnly(self, deviceName: str = "default"):
        """Pauses a specific camera device.
        Args:
            deviceName: camera device name.
        """
        if deviceName in self.devices:
            device = self.devices[deviceName]
            device.pause()

    def pauseAll(self):
        """Pauses all camera devices."""
        for device in self.devices.values():
            device.pause()

    def resumeAll(self):
        """Resumes all camera devices."""
        for device in self.devices.values():
            device.resume()

    def resumeOnly(self, deviceName: str = "default"):
        """Resumes a specific camera device.
        Args:
            deviceName: camera device name.
        """
        if deviceName in self.devices:
            device = self.devices[deviceName]
            device.resume()

    @staticmethod
    def ports():
        """Returns a list with the availables serial port devices."""
        return [port.device for port in list_ports.comports()]

    def toJson(self, data: str = ""):
        """Converts a string to a json.
        Args:
            data: a string message.
        """
        try:
            return json.loads(data)
        except Exception as e:
            print(f"-> Serials :: {e}")
            return data

    def writeTo(
        self,
        deviceName: str = "default",
        message: str = "",
        end: str = "\n",
        asJson: bool = False,
    ):
        """Writes a message to a specific serial device.
        Args:
            deviceName: name of the serial device.
            message: message to be written.
            end: newline character to be concated with the message.
            asJson: transform message to a json?
        """
        if deviceName in self.devices:
            self.device[deviceName].write(message=message, end=end, asJson=asJson)

    def write(self, message: dict = {}, end: str = "\n", asJson: bool = False):
        """Writes a message given a dict with the device name and the message.
        Args:
            message: message to be written.
            end: newline character to be concated with the message.
            asJson: transform message to a json?
        """
        for deviceName, data in message.items():
            if deviceName in self.devices:
                self.device[deviceName].write(message=data, end=end, asJson=asJson)

    def on(self, eventName: str = "", callback=None, *args, **kwargs):
        """A wrapper function for use on/emit functions. It defines a specific event
        to every serial devices listed on current instance.
        Args:
            eventName: name of the event to be signaled.
            callback: callback function
        """
        index = 0
        for device in self.devices.values():
            f = None
            # if eventName =='data':
            #     f = lambda data: callback(device.getPort(), data)
            # elif eventName == 'connection':
            #     f = lambda status: callback(device.getPort(), status)
            # elif eventName == 'ports' and index == 0:
            #     f = lambda ports: callback(device.ports())
            #     device.on(eventName, f, *args, **kwargs)
            # if  eventName == 'ports':
            #     device.on(eventName, callback, *args, **kwargs)
            device.on(eventName, callback, *args, **kwargs)
            index += 1