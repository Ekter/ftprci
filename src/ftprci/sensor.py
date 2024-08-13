import abc
import interface
import collections
import enum
import struct

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

    class OutputTypes(enum.Enum):
        """
        Possible return types of the read method.
        """
        Vector3 = collections.namedtuple('Vector3', 'x y z')
        Vector2 = collections.namedtuple('Vector2', 'x y')
        Scalar = float


    @abc.abstractmethod
    def read(self):
        """
        Read and return data from the sensor.

        Returns:
            Data read from the sensor. Can be any type.
        """

    def __init__(self):
        """
        The __init__ method should be overloaded if an initialization is needed.
        """
        return #ruff-B027

class LSM6(Sensor):
    class Regs:
        CTRL1_XL = 0x10
        CTRL2_G = 0x11
        CTRL3_C = 0x12
        OUTX_L_G = 0x22
        OUTX_L_XL = 0x28

    class RawData:
        def __init__(self, acc, gyro):
            self.acc = Sensor.OutputTypes.Vector3(*struct.unpack('hhh', bytes(acc)))
            self.gyro = Sensor.OutputTypes.Vector3(*struct.unpack('hhh', bytes(gyro)))


    def __init__(self, slave_addr=0x6B):
        """
        The LSM6 is a sensor combining an accelerometer and a gyroscope.

        The address should be 0x6A or 0x6B depending on the SDO/SA0 connection.
        """
        self.interface = interface.SMBusInterface(slave_addr)
        self.interface.send_command(LSM6.Regs.CTRL1_XL, 0x50) # 208 Hz ODR, 2 g FS
        self.interface.send_command(LSM6.Regs.CTRL2_G, 0x58) # 208 Hz ODR, 1000 dps FS
        self.interface.send_command(LSM6.Regs.CTRL3_C, 0x04) # auto increment address

    def read(self):
        gyro = self.interface.read(address=LSM6.Regs.OUTX_L_G, max_bytes=6)
        acc = self.interface.read(address=LSM6.Regs.OUTX_L_XL, max_bytes=6)

        return LSM6.RawData(acc, gyro)
