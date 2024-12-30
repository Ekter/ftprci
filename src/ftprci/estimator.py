import abc
from . import sensor
import numpy as np

class Estimator(abc.ABC):
    """
    Abstract base class for estimators.

    This class defines the interface that should be implemented by all estimators.
    The estimator generally behaves like a transformer around Sensor, processing
    raw data and returning a processed result.

    Abstract methods:
        * estimate

    Use __init__ to initialize the estimator if needed.
    """

    @abc.abstractmethod
    def estimate(self, data) -> float:
        """
        Read and return data from the estimator.

        Returns:
            Data read from the estimator.
        """

    def __init__(self):
        """
        The __init__ method should be overloaded if an initialization is needed.
        """
        return #ruff-B027

    def __call__(self, data):
        return self.estimate(data)


class DiscreteLowPassFilter(Estimator):
    """
    Discrete low pass filter.

    Alpha = e^(-dt/wc)
    """
    def __init__(self, alpha = 5, dimension = 1):
        super().__init__()
        self.alpha = alpha
        self.y = np.zeros((1, dimension))

    def estimate(self, data):
        self.y = self.y * self.alpha + data * (1 - self.alpha)
        return self.y


class DiscreteHighPassFilter(Estimator):
    """
    Discrete high pass filter.

    Alpha = 1/(dt*wc+1)
    """
    def __init__(self, alpha = 5, dimension = 1):
        super().__init__()
        self.alpha = alpha
        self.y = np.zeros((1, dimension))
        self.prev_x = np.zeros((1, dimension))

    def estimate(self, data):
        self.y = self.y * self.alpha + self.alpha *(data-self.prev_x)
        self.prev_x = data
        return self.y


class HighPassFilter(Estimator):
    """
    High pass filter(just a subtraction with the mean over some measurements)
    """
    def __init__(self, buffer_size = 5, dimension = 1):
        super().__init__()
        self.buffer = np.zeros((buffer_size, dimension))

    def estimate(self, data):
        ret = data - np.mean(self.buffer, axis=0)
        self.buffer = np.roll(self.buffer, 1, axis=0)
        self.buffer[-1] = data
        return ret


class ComplementaryFilter(Estimator):
    """
    Complementary filter on accelerometer and gyroscope data.

    Input type is `sensor.AccGyro.RawData`
    """
    def __init__(self, buf_size = 5):
        super().__init__()
        self.acc_low_pass = DiscreteLowPassFilter(buffer_size=buf_size, dimension=3)
        self.gyro_high_pass = HighPassFilter(buffer_size=buf_size, dimension=3)

    def estimate(self, data: sensor.AccGyro.RawData):
        acc = self.acc_low_pass(data.acc)
        theta_dot = self.gyro_high_pass(data.gyro)
        theta = np.acos(acc[0]/np.linalg.norm(acc))

        return theta, theta_dot


class LinearKalmanFilter(Estimator):
    def __init__(self, xhat_init, P_init, H, F, Q, R, G = None, Ts=None):
        super().__init__()
        if G is None:
            self.G = np.zeros(xhat_init.shape[0])
        else:
            self.G = G

        self.I = np.eye(xhat_init.shape[0])
        self.xhat_minus = xhat_init
        self.xhat = np.zeros(xhat_init.shape[0])
        self.P_minus = P_init
        self.P = np.zeros(P_init.shape[0])
        self.H = H
        self.F = F
        self.Q = Q
        self.R = R
        self.phi = np.eye(F.shape[0]) + F*Ts + F*F*Ts*Ts/2

    def estimate(self, data, u = None):
        if u is None:
            u=np.zeros((self.xhat.shape[0], 1))

        if self.R.shape[0] == 1:
            K = self.P_minus @ self.H.T /(self.H @ self.P_minus @ self.H.T + self.R)

        else:

            K = self.P_minus @ self.H.T @ np.linalg.inv(self.H @ self.P_minus @ self.H.T + self.R)

        self.xhat = self.xhat_minus + K @ (data - self.H @ self.xhat_minus)

        self.xhat_minus = self.phi @ self.xhat + self.G @ u

        self.P = (self.I-K @ self.H) @ self.P_minus

        self.P_minus = self.phi @ self.P @ self.phi.T + self.Q

        return self.xhat
