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


class LowPassFilter(Estimator):
    """
    Low pass filter(just a mean over some measurements)
    """
    def __init__(self, buffer_size = 5, dimension = 1):
        super().__init__()
        self.buffer = np.zeros((buffer_size, dimension))

    def estimate(self, data):
        self.buffer = np.roll(self.buffer, 1, axis=0)
        self.buffer[-1] = data
        return np.mean(self.buffer, axis=0)


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
        self.acc_low_pass = LowPassFilter(buffer_size=buf_size, dimension=3)
        self.gyro_high_pass = HighPassFilter(buffer_size=buf_size, dimension=3)

    def estimate(self, data: sensor.AccGyro.RawData):
        acc = self.acc_low_pass(data.acc)
        theta_dot = self.gyro_high_pass(data.gyro)
        theta = np.acos(acc[1]/np.linalg.norm(acc))

        return theta, theta_dot
