import numpy as np


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