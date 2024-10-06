import src.ftprci as fci
import matplotlib.pyplot as plt
import numpy as np
import math

class NoisySine(fci.Sensor):
    def __init__(self, Ts, dt, win, noise):
        self.t = np.linspace(0, Ts, int(Ts/dt))
        self.data = np.sin(self.t*win)+np.random.normal(0, noise, len(self.t))
        self.i = 0

    def read(self):
        self.i += 1
        return self.data[self.i-1]

    def reset(self):
        self.i = 0

Ts = 10
dt = 1/10
win = 3
wc = 3
noise_power = 0.1

inp = NoisySine(Ts, dt, win, noise_power)

est = fci.DiscreteLowPassFilter(alpha=math.exp(-dt/wc))

log = fci.TimedLogger()

fci.logger.pl.set_cont(sep=",")

th = fci.RunnerThread(period=dt)

th.callback | inp | est | log
