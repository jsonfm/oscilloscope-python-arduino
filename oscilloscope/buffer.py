from collections import deque


class Buffer:
    def __init__(self, name="default", max_len=1000):
        self.name = name
        self.max_len = max_len
        self.data = deque(max_len=self.max_len)

    def reset(self):
        pass

    def clear(self):
        self.data.clear()

    def getData(self):
        return self.data

    def add(self, value):
        self.data.append(value)