import abc


class Controller(abc.ABC):
    @abc.abstractmethod
    def set_order(self, order):
        """
        Set the order for the controller.

        Parameters:
            * order: Order to set.
                State.
        """

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
