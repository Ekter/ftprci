import abc

class Estimator(abc.ABC):
    """
    Abstract base class for estimators.

    This class defines the interface that should be implemented by all estimators.
    The estimator generally behaves like a wrapper around Sensor, processing raw data
    and returning a processed result.

    Abstract methods:
        * estimate

    Use __init__ to initialize the estimator if needed.
    """

    @abc.abstractmethod
    def estimate(self) -> float:
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
