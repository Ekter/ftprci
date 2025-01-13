import pretlog as pl
import numpy as np
import time


class Logger():
    def log(self, data):
        pl.default(data)
        return data

    def __call__(self, *args, **kwds):
        return self.log(*args, **kwds)

class TimedLogger(Logger):
    def log(self, data):
        pl.default(time.asctime(time.localtime()), data)
        return data


class DataComparativeLogger(Logger):
    def __init__(self, min_: np.ndarray, max_: np.ndarray):
        super().__init__()
        self.min_ = min_
        self.max_ = max_

    def log(self, data):
        for i in range(len(data)):
            if data[i] < self.min_[i] or data[i] > self.max_[i]:
                pl.error(data[i], end=" ")
            else:
                pl.valid(data[i], end=" ")
        pl.default()
        return data


class PlotLogger(TimedLogger):
    def __init__(self, update_freq=1):
        super().__init__()
        self.update_freq = update_freq
        self.data = []
        self.t = []
        self.i = 0

    def log(self, data):
        self.data.append(data)
        self.t.append(time.time())
        self.i += 1
        if self.i % self.update_freq == 0:
            import matplotlib.pyplot as plt

            plt.plot(self.t, self.data)
            plt.pause(1e-9)
        return super().log(data)
