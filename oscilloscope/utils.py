import numpy as np
import time


class SamplerTimeCounter:
    """Records the time interval between samples."""
    def __init__(self):
        self.lastTime = 0
        self.currentTime = 0
        self.elapsed = 0
    
    def interval(self):
        """Calculates the elapsed time interval between the last measurement and the current one. (secs)."""
        self.lastTime = self.currentTime
        self.currentTime = time.time()
        self.elapsed = self.currentTime - self.lastTime
        return self.elapsed

    def frequency(self):
        """Calculates the frequency of the measurement time. (Hz)."""
        try:
            return 1 / self.interval()
        except Exception as e:
            return 0

    def lastInterval(self):
        """Returns the last measured time interval (secs)."""
        return self.elapsed

    def lastFrequency(self):
        """Returns the last measured frequency. (Hz)."""
        try:
            return 1 / self.elapsed
        except:
            return 0

    def update(self):
        """Updates the time measurement."""
        self.interval()

    def clear(self):
        """Clears internal variables."""
        self.lastTime = 0
        self.currentTime = 0


class TimerCount:
    """Counts elapsed time in seconds and checks if an interval of time had happen.
    
    Args:
        interval: time interval in seconds
        callback: it will be called when the time interval have been reached
    
    """
    def __init__(self, interval: float = 1.0, callback = None):
        self.interval = interval
        self.callback = callback
        self.time = 0
        self.initial = 0
        self.ready = False
    
    def update(self):
        """Updates the time count."""
        if self.initial == 0:
            self.initial = time.time()
        
        # Interval have been reached
        if time.time() - self.initial >= self.interval:
            if self.callback is not None:
                self.callback()
            self.initial = 0
            self.ready = True
    
    def isReady(self):
        """Checks if the time interval was reached."""
        return self.ready
    
    def reset(self):
        """Resets the timer."""
        self.initial = 0
        self.ready = False
        

def magnitudeSpectrum(x, dt=1, Fs=1):
    N = len(x)
    T = int(Fs * N)
    f = np.linspace(0, Fs, N / 2 )
    xf = np.fft.fft(x)
    mag = (2.0 / N) * np.abs(xf[: N // 2])
    return mag

def dbScale(x):
    xdb = 20 * np.log10(x)
    return xdb