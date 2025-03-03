import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("qtagg")
import time

from src.ftprci import Clock, ClockedPlotLogger1D, ProgressBar

beg = time.time()
t = lambda _: time.time() - beg

for i in range(6):
    beg = time.time()

    fig = plt.figure(i)
    c = Clock(10 ** (-i), 10)
    ax = [fig.add_subplot(1, 1, 1)]
    ax[0].set_yscale("log")
    pl = ClockedPlotLogger1D(c, ax, 10 ** (i + 1))
    pr = ProgressBar(c)

    c >> pr | t | pl
    c.start()
    c.wait()
    plt.show()
