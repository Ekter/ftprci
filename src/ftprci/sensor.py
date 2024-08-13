import abc


class Sensor(abc.ABC):
    """
    Abstract base class for sensors.

    This class defines the interface that should be implemented by all sensors.
    The sensor generally behaves like a wrapper around Interface, waiting for commands
    and returning raw data.

    Abstract methods:
        * read

    Use __init__ to initialize the sensor if needed.
    """

    @abc.abstractmethod
    def read(self) -> float:
        """
        Read and return data from the sensor.

        Returns:
            Data read from the sensor.
        """

    def __init__(self):
        """
        The __init__ method should be overloaded if an initialization is needed.
        """
        return #ruff-B027
