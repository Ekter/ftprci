"""
Interface module.

The -Interface classes are used to communicate with the physical system.

They can be either USB, I2C, physical output for compatible systems, or any other type of interface.
"""


import time
import abc
import pretlog as pl
import smbus

class Interface(abc.ABC):
    """
    Abstract base class for interfaces.

    This class defines the interface that should be implemented by all interfaces.
    The interface behaves like a master device, sending commands and reading data
    from the physical system, but it can also be used as a slave via polling.

    Abstract methods:
        * send_command
        * read
        * ping
    """

    @abc.abstractmethod
    def send_command(self, *command, address=0):
        """
        Send a command through the interface.

        Parameters:
            * command: Command to send.
        """

    @abc.abstractmethod
    def read(self, *, address=0, max_bytes = 1024):
        """
        Read and return data from the interface.

        Parameters:
            * max_bytes: Maximum number of bytes to read. Default is 1024.

        Returns:
            Data read from the interface.
        """

    def ping(self) -> float:
        """
        Ping through the interface and return the time it took to get a response.

        Returns:
            Time in seconds it took to get a response.
        """
        raise NotImplementedError("Please implement the ping method for your subclass.")


class SMBusInterface(Interface):
    """
    Interface class for the SMBus protocol.
    """
    def __init__(self, slave_addr) -> None:
        self.bus = smbus.SMBus(1)
        self.sa = slave_addr

    def send_command(self, *commands, address=0, data:bool = False, block: bool = False):
        """
        Send commands through the interface.

        Parameters:
            * command : Commands to send.
        """
        if block:
            self.bus.write_i2c_block_data(self.sa, address, commands)
            return
        if not data:
            self.bus.write_byte(self.sa, address, *commands)
        else:
            self.bus.write_byte_data(self.sa, address, *commands)

    def read(self, *, address=0x22, max_bytes = 1024):
        """
        Read and return data from the interface.

        Parameters:
            * address: Register to read from. Default is 0x22.
            * max_bytes: Maximum number of bytes to read. Default is 1024.

        Returns:
            Data read from the interface.
        """
        return self.bus.read_i2c_block_data(self.sa, address, max_bytes)

# class I2CInterface(Interface):
#     """
#     Interface class for the I2C protocol
#     """


class DummyInterface(Interface):
    """
    Dummy interface intended for debugging and testing purposes.

    This interface will only send commands to the terminal.

    Overloaded abstract methods:
        * send_command
        * read
        * ping
    """
    def __init__(self, timeout=1, no_warn=False) -> None:
        if not no_warn:
            pl.warn(
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
        pl.warn("Malformed ping response.")
        return time.time()-t

    def read(self, *, max_bytes = 1024):
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
        time.sleep(2)
        pl.default(f"ping:{dummy.ping()}")
