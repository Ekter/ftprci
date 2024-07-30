"""
Interface module.

The -Interface classes are used to communicate with the physical system.

They can be either USB, I2C, physical output for compatible systems, or any other type of interface.
"""


import time
import abc
import col


class Interface(abc.ABC):
    """
    Abstract base class for interfaces.

    This class defines the interface that should be implemented by all interfaces.
    """
    @abc.abstractmethod
    def send_command(self, command):
        """
        Send a command through the interface.

        Parameters:
            * command: Command to send.
        """

    @abc.abstractmethod
    def read(self, max_bytes = 1024):
        """
        Read and return data from the interface.

        Parameters:
            * max_bytes: Maximum number of bytes to read. Default is 1024.
        
        Returns:
            Data read from the interface.
        """

    @abc.abstractmethod
    def ping(self) -> float:
        """
        Ping through the interface and return the time it took to get a response.

        Returns:
            Time in seconds it took to get a response.
        """



class DummyInterface:
    """
    Dummy interface intended for debugging and testing purposes.

    This interface will only send commands to the terminal.

    Over
    """
    def __init__(self, timeout=1, no_warn=False) -> None:
        if not no_warn:
            col.warn(
                """ Warning! This interface will only send commands to the terminal.
                \n  It is not connected to any physical system.
                \n  Use a derived class to connect to a physical system, like
                    USBInterface or I2CInterface.
                \n  To suppress this warning, pass no_warn=True to the constructor."""
            )
        self.timeout = timeout
        self.ping_answer = "pong"

    def send_command(self, command):
        """
        Send a command through the interface.
        """
        print(f"Sending command to terminal: {command}")

    def ping(self) -> float:
        """
        Ping through the interface and return the time it took to get a response.

        Returns:
            Time in seconds it took to get a response.
        """
        t = time.time()
        self.send_command("ping")
        if self.read() == self.ping_answer:
            return time.time()-t
        col.warn("Malformed ping response.")
        return time.time()-t

    def read(self, max_bytes = 1024):
        """
        Read and return data from the interface.

        Parameters:
            * max_bytes: Maximum number of bytes to read. Default is 1024.
        
        Returns:
            Data read from the interface.
        """
        return input("Enter command response: ")[:max_bytes]



if __name__=="__main__":
    # Test the DummyInterface class
    dummy = DummyInterface()
    dummy.send_command("test")
    while True:
        col.default(f"ping:{dummy.ping()}")
