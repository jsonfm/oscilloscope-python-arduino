import time
import os
from collections import deque
import pandas as pd
import random
from .sevent import Emitter


class Buffer(Emitter):
    """Buffer class to storage a signal

    :param name: name of the buffer/signal
    :param maxlen: signal length

    """
    def __init__(self, name:str="x", maxlen:int=10000, autoclear:bool=False, timed:bool=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert name!='t', 'Not valid Name, please Try with someone different of <<t>>'
        self.name = name
        self.maxlen = maxlen
        self.defaultMaxLen = maxlen
        self.autoclear = autoclear
        self.timed = timed
        self.data = deque(maxlen=self.maxlen)
        self.time = None
        self.lastTime = 0
        if self.timed:
            self.time = deque(maxlen=self.maxlen)

    def __len__(self):
        return len(self.data)

    def reset(self):
        """It resets the current buffer."""
        self.maxlen = self.defaultMaxLen
        self.data = deque(maxlen=self.maxlen)
        if self.sampleTimeEnabled():
            self.time = deque(maxlen=self.maxlen)
    
    def setNewLen(self, length:int):
        """It updates the length of the buffer.
        
        :param length: new value of the length.
        """
        self.maxlen = length
        self.data = deque(maxlen=length)

    def isFull(self):
        """It checks if the buffer is full."""
        return len(self.data) == self.maxlen - 1
 
    def sampleTimeEnabled(self):
        """It checks if the sample time is enabled."""
        return self.timed and self.time is not None

    def clear(self, timeToo:bool=True):
        """It clears the current data.

        :param timeToo: clear the variable buffer too.
        """
        self.data.clear()
        if timeToo:
            if self.time is not None:
                self.time.clear()

    def getData(self):
        """It returns the current data."""
        return self.data

    def getTime(self):
        """It returns the current time vector."""
        return self.time

    def getDataAndTime(self):
        data = {self.name: self.getData(), 't': self.getTime()}
        return data

    def sampleTime(self):
        if self.sampleTimeEnabled():
            if len(self.time) == 0:
                self.lastTime = time.time()
                self.time.append(0)
            else:
                currentTime = time.time()
                dt = currentTime - self.lastTime
                self.time.append(dt)
    
    def notifyIsFull(self):
        """If the buffer is full it will emit an event signal."""
        if self.isFull():
            self.emit('is-full', self.data)
            if self.autoclear:
                self.data.clear()
                if self.time is not None:
                    self.time.clear()

    def append(self, value):
        """It appends a new value to the data list/deque.
        
        :param value: new value to add to the data.
        """
        self.data.append(value)
        self.sampleTime()
        self.notifyIsFull()

    def save(self, filename:str, folder:str):
        """It saves as csv the current data.

        :param filename: name of the file to be written.
        :param folder: name of the folder.
        """
        try:
            data = {self.name: self.data}
            df = pd.DataFrame(data)
            filepath = os.path.join(folder, filename)
            df.to_csv(filepath)
        except Exception as e:
            print(e)

    def fill(self, data:list):
        """It fills the current list of data, with a passed list/deque.
        
        :param data: new data to update the internal data list/deque
        """
        self.data = deque(data)
        if len(data) < self.maxlen:
            self.maxlen = self.defaultMaxLen

    def load(self, filepath:str):
        """It loads data from a csv file.
        
        :param filepath: file directory.
        """
        df = pd.read_csv(filepath, index_col=0)
        data = df[self.name].values
        self.fill(data)
    

class MultipleBuffers(Emitter):
    """A class for manage multiples buffer at same time.

    :param variables: a list with the name of the variables to create a buffer.
    :param timed: sample time?
    :param maxlen: maximum length of each buffer created.
    """
    def __init__(self, variables:list=['x'], timed:bool=False, maxlen:bool=10000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.variables = {}
        self.mainKey = ""
        for i in range(len(variables)): 
            key = variables[i]
            if i == 0:
                self.mainKey = key
            buffer = Buffer(name=key, timed=False, maxlen=maxlen, *args, **kwargs)
            self.variables[key] = buffer

        self.defaultMaxLen = maxlen   
        self.maxlen = maxlen
        self.timed = timed
        self.time = None

        if self.timed:
            self.time = deque(maxlen=self.maxlen)

        self.lastTime = 0
    
    def __getitem__(self, key):
        return self.variables[key]
    
    def __len__(self):
        return len(self.variables)
    
    def keys(self):
        return self.variables.keys()

    def values(self):
        return self.variables.values()

    def resetAll(self):
        for buffer in self.variables.values():
            buffer.reset()
        self.maxlen = self.defaultMaxLen
        if self.sampleTimeEnabled():
            self.time = deque(maxlen=self.maxlen)

    def sampleTimeEnabled(self):
        return self.timed and self.time is not None

    def sampleTime(self):
        if self.sampleTimeEnabled():
            if len(self.time) == 0:
                self.lastTime = time.time()
                self.time.append(0)
            else:
                currentTime = time.time()
                dt = currentTime - self.lastTime
                self.time.append(dt)

    def appendAll(self, data:dict):
        """It appends multiple variables values at the same time passing a dictinary with the keys/names and the corresponding values.
        
        :param data: a dictinary with new variables values.
        """
        error = False
        for key, value in data.items():
            try:
                self.variables[key].append(value)
            except KeyError as e:
                error = True
                print(e)

        if not error:
            self.sampleTime()
    
    def lenOf(self, key):
        """It returns the len of."""
        if key in self.variables:
            return len(self.variables[key])

    def appendTo(self, key:str, value):
        """It appends a new value to a specific variable buffer."""
        if key in self.variables:
            self.variables[key].append(value)

    def clearAll(self):
        """It clears every variable buffer."""
        for buffer in self.variables.values():
            buffer.clear()
    
    def getDataOfAll(self):
        """It returns a dictionary with all data saved so far."""
        data = {}
        for key in self.variables:
            data[key] = self.variables[key].getData()
        return data

    def getTime(self):
        """It returns the current time vector."""
        return self.time

    def getDataAndTime(self):
        """It returns a dict with data and time."""
        allData = self.getDataOfAll()
        allData['t'] = self.getTime()
        return allData

    def getDataOf(self, key:str):
        """It returns the data of a specific buffer/variable."""
        if key in self.variables:
            return self.variables[key].getData()

    def saveAll(self, name="default.csv"):
        """It saves all data storaged in all variables/buffer on a single CSV file."""
        if self.time:
            data = self.getDataAndTime()
        else:
            data = self.getDataOfAll()
        df = pd.DataFrame(data)
        df.to_csv(name)
    
    def load(self, filepath:str):
        """It loads all variables contained on one single CSV file."""
        try:
            df = pd.read_csv(filepath, index_col=0)
            columns = df.columns.values
            self.variables = {}
            for column in columns:
                data = df[column].values
                buffer = Buffer(name=column)
                buffer.fill(data)
                self.variables[column] = buffer
        except Exception as e:
            print(e)

    def saveOnly(self, key:str, filepath:str, name:str):
        """It saves the data of only one buffer/variable."""
        if key in self.variables:
            self.variables[key].save(filepath, name)
    
    def infoLen(self):
        """It displays info about length of the signals."""
        print(" __________ SHOWING LEN INFO _____________")
        for buffer in self.variables.values():
            print(f"{buffer.name} : ", len(buffer))

        if self.sampleTimeEnabled():
            print('time: ', len(self.time))

    def addEventTo(self, key:str, event:str, callback):
        """It adds and event to a specific buffer"""
        if key in self.variables:
            self.variables[key].on(event, callback)

    def getBuffer(self, key):
        if key in self.variables:
            return self.variables[key]

    def setNewLen(self, length:int):
        """It sets a new length for all buffers."""
        self.maxlen = length
        self.time = deque(maxlen=self.maxlen)
        for buffer in self.variables.values():
            buffer.setNewLen(length)

# b = MultipleBuffers(variables=['x', 'y'], timed=True, maxlen=10)
# b.on('is-full', lambda: print(b.getDataAndTime))
# b['x'].on('is-full', lambda data: print('hola: ', data))
# for i in range(10):
#     x = random.randint(1, 10)
#     y = random.randint(1, 10)
#     data = {'x': x, 'y': y}
#     b.appendAll(data)
#     time.sleep(.25)
# data = b.getDataAndTime()
# print(data)
# print(b.infoLen())