import src.ftprci as fci
import matplotlib.pyplot as plt
import numpy as np
import math
import time

class FallingObjectRadar(fci.Sensor):
    def __init__(self, x0, v0, a, dt, noise):
        self.previous_xdot = np.array([0, 0])
        self.xdot = np.array([0, 0])
        self.state = np.array([x0, v0])
        self.a = a
        self.dt = dt
        self.noise = noise
        self.A = np.array([[1, dt], [0, 1]])

    def read(self):
        self.xdot = self.A @ self.previous_xdot + np.array([0, self.a*self.dt])
        self.state = self.state + (self.xdot/2+self.previous_xdot/2)*self.dt
        return self.state


class PlotterLogger(fci.Logger):
    def __init__(self):
        super().__init__()
        self.data = []

    def log(self, data):
        self.data.append(data)

    def plot(self):
        plt.plot(self.data)
        plt.show()

Ts = 1
dt = 1/10
noise_power = 0.1

radar = FallingObjectRadar(122000, -1800, -9.81, dt, noise_power)

P_init = np.array([[10**9, 0], [0, 10**9]])
X_init = np.array([0, 0]).T
H = np.array([1, 0])
F = np.array([[0, 1], [0, 0]])
Q = np.array([[0, 0], [0, 0]])
R = np.array([300**2])
G = np.array([0, 0])

est = fci.LinearKalmanFilter(X_init, P_init, H, F, Q, R, G, dt)

log = PlotterLogger()

fci.logger.pl.set_cont(sep=",")

th = fci.RunnerThread(period=dt)

th.callback | radar | est | log


time.sleep(Ts)

log.plot()
