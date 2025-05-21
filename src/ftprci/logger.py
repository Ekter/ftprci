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
        def __init__(self, dimension=3):
            self.values = [[] for _ in range(dimension)]

        def new_value(self, value):
            for series, data in zip(self.values, value):
                series.append(data)

        def get_values(self):
            return self.values

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
        def __init__(self, dimension=3):
            super().__init__(dimension=dimension)
            self.time = []

        def new_value(self, value, time_value):
            super().new_value(value)
            self.time.append(time_value)

        def get_values(self):
            return self.time, self.values

    def __init__(
        self,
        clock,
        fig,
        legend: str = "",
        update_freq=1,
        plot_num=1,
        dimension=3,
        style="o",
    ):
        super().__init__(clock)
        self.legend = legend
        self.num_plot = plot_num
        self.dimension = dimension
        self.update_freq = update_freq
        self.style = style
        if isinstance(fig, Iterable):
            self.ax = fig
        else:
            self.ax = []
            for i in range(plot_num):
                for d in range(dimension):
                    self.ax.append(
                        fig.add_subplot(dimension, plot_num, i + 1 + d * plot_num)
                    )
        self.data = [self.Data(dimension) for _ in range(plot_num)]

    def log(self, data: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        if (
            data.shape[0] == self.dimension
            and len(data.shape) == 1
            or data.shape[1] == self.num_plot
        ):
            for i in range(self.num_plot):
                self.data[i].new_value(data[:, i], self.clock.t)
        elif data.shape[0] == self.num_plot and data.shape[1] == self.dimension:
            for i in range(self.num_plot):
                self.data[i].new_value(data[i, :], self.clock.t)
        else:
            raise ValueError("Data shape is not correct")
        return data

    def plot(self):
        for i in range(self.num_plot):
            times, values = self.data[i].get_values()
            for index, series in enumerate(values):
                self.ax[i + index * self.num_plot].plot(
                    times, series, label=self.legend
                )
                self.ax[i + index * self.num_plot].legend(loc="upper left")


class ProgressBar(ClockedLogger):
    def __init__(self, clock: Clock):
        super().__init__(clock)
        self.pbar = tqdm.tqdm(total=self.clock.length)

    def log(self, data):
        self.pbar.update()
        return data
