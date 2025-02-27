import time

import numpy as np
import pretlog as pl
import tqdm


class Logger:
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


class PlotLogger1D(Logger):
    def __init__(self, ax, update_freq=1):
        super().__init__()
        self.update_freq = update_freq
        self.data = []
        self.t = []
        self.i = 0
        self.ax = ax

    def log(self, data):
        self.data.append(data)
        self.t.append(time.time())
        self.i += 1
        if self.i % self.update_freq == 0:
            self.ax.plot(self.t, self.data)
            self.ax.pause(1e-9)
        return super().log(data)


class PlotLogger3D(PlotLogger1D):
    class Data:
        def __init__(self):
            self.x = []
            self.y = []
            self.z = []

        def new_value(self, value):
            self.x.append(value[0])
            self.y.append(value[1])
            self.z.append(value[2])

        def get_values(self):
            return self.x, self.y, self.z

    def __init__(self, ax, update_freq=1):
        super().__init__(ax, update_freq)
        self.data = PlotLogger3D.Data()

    def log(self, data):
        self.data.new_value(data)
        # self.t.append(time.time())
        self.i += 1
        if self.i % self.update_freq == 0:
            self.ax.scatter(*self.data.get_values())
            # self.ax.pause(1e-9)
        return data


class ProgressBar(Logger):
    def __init__(self, clock):
        super().__init__()
        self.clock = clock
        self.pbar = tqdm.tqdm(total=clock.t_max / clock.dt)
        self.times = np.zeros(int(clock.t_max / clock.dt))
        self.i = 0

    def log(self, data):
        self.pbar.update(self.clock.t)
        # self.i += 1
        # assert self.i == int(self.clock.t/self.clock.dt)
        # c_time = time.time()
        self.times[round(self.clock.t / self.clock.dt)] = time.time()
        return data

    def plot(self, ax):
        ax.plot(range(len(self.times)), self.times)
        ax.set_title("Time taken for each iteration")
