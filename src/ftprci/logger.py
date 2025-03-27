import time
from typing import Iterable, TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt
import pretlog as pl
import tqdm

from .main import Clock

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from matplotlib.axes import Axes

PrintableT = Any
"Type with a __repr__ or __str__ method, allowing print method."


class Logger:
    def log(self, data: PrintableT) -> PrintableT:
        pl.default(data)
        return data

    def __call__(self, *args, **kwds):
        return self.log(*args, **kwds)


class TimedLogger(Logger):
    def log(self, data: PrintableT) -> PrintableT:
        pl.default(time.asctime(time.localtime()), data)
        return data


class ClockedLogger(Logger):
    def __init__(self, clock: Clock):
        super().__init__()
        self.clock = clock

    def log(self, data: PrintableT) -> PrintableT:
        pl.default(self.clock.t, data)
        return data


class DataComparativeLogger(Logger):
    def __init__(self, min_: npt.NDArray[np.number], max_: npt.NDArray[np.number]):
        super().__init__()
        self.min_ = min_
        self.max_ = max_

    def log(self, data: npt.NDArray[np.number]) -> float:
        for index, value in enumerate(data):
            if value < self.min_[index] or value > self.max_[index]:
                pl.error(data[index], end=", ")
            else:
                pl.valid(data[index], end=", ")
        pl.default()
        return data


class TimedPlotLogger1D(TimedLogger):
    def __init__(self, fig, update_freq=1):
        super().__init__()
        self.update_freq = update_freq
        self.data = []
        self.t = []
        self.i = 0
        if isinstance(fig, Iterable):
            self.ax = fig
        else:
            self.ax = []
            self.ax.append(fig.add_subplot())

    def log(self, data):
        self.data.append(data)
        self.t.append(time.time())
        self.i += 1
        if self.i % self.update_freq == 0:
            self.ax.plot(self.t, self.data)
            # self.ax.pause(1e-9)
        return data


class ClockedPlotLogger1D(ClockedLogger):
    class Data:
        def __init__(self):
            self.values = []
            self.time = []

        def new_value(self, value, time_value):
            self.values.append(value)
            self.time.append(time_value)

        def get_values(self):
            return self.time, self.values

    def __init__(self, clock, fig, update_freq=1, dimension=1):
        super().__init__(clock)
        self.dimension = dimension
        self.update_freq = update_freq
        if isinstance(fig, Iterable):
            assert len(fig) >= dimension
            self.ax = fig
        else:
            self.ax = []
            for i in range(dimension):
                self.ax.append(fig.add_subplot(1, dimension, i + 1))
        self.i = 0
        self.data = [self.Data() for _ in range(dimension)]

    def log(self, data):
        if isinstance(data, (int, float)):
            data = np.array([[data]])
        if (
            data.shape[0] == 1
            and len(data.shape) == 1
            or data.shape[1] == self.dimension
        ):
            for i in range(self.dimension):
                self.data[i].new_value(data[:, i], self.clock.t)
        elif data.shape[0] == self.dimension and data.shape[1] == 1:
            for i in range(self.dimension):
                self.data[i].new_value(data[i, :], self.clock.t)
        else:
            raise ValueError("Data shape is not correct")

        self.i += 1
        if self.i % self.update_freq == 0:
            for i in range(self.dimension):
                times, values = self.data[i].get_values()
                self.ax[i].plot(times, values)
        return data


class FourierClockedPlotLogger1D(ClockedPlotLogger1D):
    def __init__(self, clock, fig, update_freq=1, dimension=1, log_scale=False):
        super().__init__(clock, fig, update_freq, dimension)
        if log_scale:
            for ax in self.ax:
                ax.set_yscale("log")

    def log(self, data):
        for i in range(self.dimension):
            self.data[i].new_value(data[i], self.clock.t)

        self.i += 1
        if self.i % self.update_freq == 0:
            for i in range(self.dimension):
                times, values = self.data[i].get_values()
                values = np.fft.fft(values)
                self.ax[i].plot(times, abs(values))
        return data


class PlotLogger3D(Logger):
    class Data:
        def __init__(self):
            self.x = []
            self.y = []
            self.z = []
            # self.style = []

        def new_value(self, value):
            self.x.append(value[0])
            self.y.append(value[1])
            self.z.append(value[2])
            # self.style.append(self.styles[0])

        def get_values(self):
            return self.x, self.y, self.z

    styles = [
        "o",
        "x",
        "+",
        "s",
        "D",
        "v",
        "^",
        "<",
        ">",
        "p",
        "P",
        "*",
        "h",
        "H",
        "X",
        "d",
    ]

    def __init__(self, fig, update_freq=1, dimension=1):
        super().__init__()
        self.dimension = dimension
        self.update_freq = update_freq
        if isinstance(fig, Iterable):
            self.ax = fig
        else:
            self.ax = []
            self.ax.append(fig.add_subplot(projection="3d"))
        self.i = 0

        self.data = [self.Data() for _ in range(dimension)]
        self.style = [
            PlotLogger3D.styles[i % len(PlotLogger3D.styles)] for i in range(dimension)
        ]

    def log(self, data):
        if data.shape[0] == 3 and data.shape[1] == self.dimension:
            for i in range(self.dimension):
                self.data[i].new_value(data[:, i])
        elif data.shape[0] == self.dimension and data.shape[1] == 3:
            for i in range(self.dimension):
                self.data[i].new_value(data[i, :])
        else:
            raise ValueError("Data shape is not correct")
        self.i += 1
        if self.i % self.update_freq == 0:
            for i in range(self.dimension):
                self.ax[0].scatter(*self.data[i].get_values(), marker=self.style[i])
        return data


class ClockedMultiPlotLogger3D(ClockedLogger):
    class Data(PlotLogger3D.Data):
        def __init__(self):
            super().__init__()
            self.time = []

        def new_value(self, value, time_value):
            super().new_value(value)
            self.time.append(time_value)

        def get_values(self):
            return self.time, self.x, self.y, self.z

    def __init__(self, clock, fig, legend: str="", update_freq=1, dimension=1):
        super().__init__(clock)
        self.legend = legend
        self.dimension = dimension
        self.update_freq = update_freq
        if isinstance(fig, Iterable):
            self.ax = fig
        else:
            self.ax = []
            for i in range(dimension):
                self.ax.append(fig.add_subplot(3, dimension, i + 1))
                self.ax.append(fig.add_subplot(3, dimension, i + 1 + dimension))
                self.ax.append(fig.add_subplot(3, dimension, i + 1 + 2 * dimension))
        self.i = 0
        self.data = [self.Data() for _ in range(dimension)]

    def log(self, data: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        if (
            data.shape[0] == 3
            and len(data.shape) == 1
            or data.shape[1] == self.dimension
        ):
            for i in range(self.dimension):
                self.data[i].new_value(data[:, i], self.clock.t)
        elif data.shape[0] == self.dimension and data.shape[1] == 3:
            for i in range(self.dimension):
                self.data[i].new_value(data[i, :], self.clock.t)
        else:
            raise ValueError("Data shape is not correct")
        self.i += 1
        if self.i % self.update_freq == 0:
            for i in range(self.dimension):
                times, xs, ys, zs = self.data[i].get_values()
                self.ax[i].plot(times, xs, label=self.legend)
                self.ax[i].legend(loc="upper left")
                self.ax[i + self.dimension].plot(times, ys, legend=self.legend)
                self.ax[i + self.dimension].legend(loc="upper left")
                self.ax[i + 2 * self.dimension].plot(times, zs, legend=self.legend)
                self.ax[i + 2 * self.dimension].legend(loc="upper left")
        return data


class ProgressBar(ClockedLogger):
    def __init__(self, clock: Clock):
        super().__init__(clock)
        self.pbar = tqdm.tqdm(total=self.clock.length)

    def log(self, data):
        self.pbar.update()
        return data
