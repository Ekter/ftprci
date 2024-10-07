import abc
# import enum
import numpy as np

class DiscreteIntegral:
    class EulerF:
        """
        Discretize using Euler Forward method.

        Equivalent to `Discretizer.HighOrd(weights=[1])`.
        """
        def __init__(self, dt = 1/1000, initial_condition = 0) -> None:
            self.accumulator = initial_condition
            self.dt = dt

        def __call__(self, new):
            self.accumulator += new*self.dt
            return self.accumulator


    class EulerB:
        """
        Discretize using Euler Backward method.

        Equivalent to `Discretizer.HighOrd(weights=[0, 1])`.
        """
        def __init__(self, dt = 1/1000, initial_condition = 0) -> None:
            self.accumulator = initial_condition
            self.dt = dt
            self.previous = 0

        def __call__(self, new):
            self.accumulator += self.previous*self.dt
            self.previous = new
            return self.accumulator


    class Tustin:
        """
        Discretize using Tustin method.

        Equivalent to `Discretizer.HighOrd(weights=[1/2, 1/2])`.
        """
        def __init__(self, dt = 1/1000, initial_condition = 0) -> None:
            self.accumulator = initial_condition
            self.dt = dt
            self.previous = 0

        def __call__(self, new):
            self.accumulator += (self.previous+new)/2*self.dt
            self.previous = new
            return self.accumulator


    class HighOrd:
        def __init__(self, dt = 1/1000, initial_condition = 0, weights = [1/6, 1/3, 1/2]) -> None: # todo remove mutable
            self.accumulator = initial_condition
            self.dt = dt
            self.weights = np.array(weights)
            self.previouses = np.zeros_like(self.weights)

        def __call__(self, new):
            self.previouses = np.roll(self.previouses, 1)
            self.previouses[-1] = new
            self.accumulator += (self.previouses*self.weights)*self.dt
            return self.accumulator


class DiscreteDifferential:
    def __init__(self) -> None:
        self.previous_val = 0

    def __call__(self, new):
        ret = new - self.previous_val
        self.previous_val = new
        return ret


class Controller(abc.ABC):
    def __init__(self) -> None:
        self.order=0

    def set_order(self, order):
        """
        Set the order for the controller.

        Parameters:
            * order: Order to set.
                State.
        """
        self.order = order

    @abc.abstractmethod
    def steer(self, state):
        """
        Steer the controller.

        Parameters:
            * state: Current state.
        """

    def update(self):
        """
        Update the controller if needed.
        """
        return # for ruff-B027


class PIDController(Controller):
    def __init__(self, p, i, d, integrator: DiscreteIntegral = None):
        self.order = 0
        self.p = p
        self.i = i
        self.d = d
        if integrator is None:
            self.integrator = DiscreteIntegral.Tustin()
        else:
            self.integrator = integrator
        self.derivative = DiscreteDifferential()

    def steer(self, state):
        epsilon = self.order-state
        return epsilon*self.p+self.i*self.integrator(epsilon)+self.d*self.derivative(epsilon)


class LQRController(Controller):
    def __init__(self, weights) -> None:
        self.weights = np.array(weights)

    def steer(self, state):
        epsilon = np.array(self.order-state)
        return epsilon*self.weights
