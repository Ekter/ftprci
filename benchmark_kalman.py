# import math
import time
import matplotlib.pyplot as plt
import numpy as np
import src.ftprci as fci

class FallingObjectRadarTustin(fci.Sensor):
    def __init__(self, x0, v0, a, dt, noise):
        self.previous_xdot = np.array([0, 0])
        self.xdot = np.array([0, 0])
        self.state = np.array([x0, v0])
        self.a = a
        self.dt = dt
        self.noise = noise
        self.A = np.array([[0, 1], [0, 0]])
        self.t = 0

    def read(self):
        self.xdot = self.A @ self.state + np.array([0, self.a*self.dt])
        self.state = self.state + (self.xdot/2+self.previous_xdot/2)*self.dt
        self.previous_xdot = self.xdot
        self.t +=self.dt
        return self.state, self.t

class FallingObjectRadarDiscrete(fci.Sensor):
    def __init__(self, x0, v0, a, dt, noise):
        self.previous_xdot = np.array([0, 0])
        self.xdot = np.array([0, 0])
        self.state = np.array([x0, v0])
        self.a = a
        self.dt = dt
        self.noise = noise
        self.A = np.array([[1, dt], [0, 1]])
        self.t = 0

    def read(self):
        self.state = self.A @ self.state + np.array([1/2*(self.dt**2)*self.a, self.a*self.dt])
        self.t +=self.dt
        return self.state, self.t



class PlotterLogger(fci.Logger):
    def __init__(self):
        super().__init__()
        self.data = []

    def log(self, *data):
        self.data.append(list(data))

    def plot(self):
        plt.plot(self.data)
        plt.show()

TS = 10
DT = 1/10
noise_power = 0.1

radar = FallingObjectRadarDiscrete(122000, -1800, -9.81, DT, noise_power)

P_init = np.array([[10**9, 0], [0, 10**9]])
X_init = np.array([0, 0]).T
H = np.array([1, 0])
F = np.array([[0, 1], [0, 0]])
Q = np.array([[0, 0], [0, 0]])
R = np.array([300**2])
G = np.array([0, 0])

est = fci.LinearKalmanFilter(X_init, P_init, H, F, Q, R, G, DT)

log = PlotterLogger()

fci.logger.pl.set_cont(sep=",")

th = fci.RunnerThread(period=DT)

th.callback | radar | (lambda x:est(x[0]), lambda _:_) | log


time.sleep(TS)

log.plot()
