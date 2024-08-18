import abc
import collections
import struct
import enum
import random
import math
from . import interface

class Sensor(abc.ABC):
    """
    Abstract base class for sensors.

    This class defines the interface that should be implemented by all sensors.
    The sensor generally behaves like a wrapper around `Interface`, waiting for commands
    and returning raw data.

    Abstract methods:
    * `read`: read data from the sensor.

    Use `__init__` to initialize the sensor if needed.

    Member classes:
    * `OutputTypes`:
        Class of possible types of numbers.
        Utility to forge complex `RawData` structures.
    * `RawData`:
        Struct for sensors output values. Each sensor should implement its own
        `RawData` class potentially using `OutputTypes` if needed.
    """

    class OutputTypes:
        """
        Possible return types of the read method.

        Utility to forge complex RawData structures.
        """
        Vector3 = collections.namedtuple('Vector3', 'x y z')
        Vector2 = collections.namedtuple('Vector2', 'x y')
        Scalar = float
        Number = int


    class RawData:
        pass


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

    def __call__(self, *args):
        self.read(*args)

    def __or__(self, other):
        return self, other


class Accelerometer(Sensor):
    class RawData:
        def __init__(self, acc=(0, 0, 0)):
            self.acc = Sensor.OutputTypes.Vector3(*acc)


class Gyrometer(Sensor):
    class RawData:
        def __init__(self, acc=(0, 0, 0)):
            self.acc = Sensor.OutputTypes.Vector3(*acc)


class Encoder(Sensor):
    class RawData:
        def __init__(self, turns):
            self.turns = turns


class AccGyro(Accelerometer, Gyrometer):
    """
    Class for one-board dual sensors containing an accelerometer and a gyroscope.

    Example: LSM6

    `RawData` is `(Vector3, Vector3)`
    """
    class RawData:
        """
        Class for storing the output of combined accelerometers and gyroscopes.

        Just has the two of them combined.

        Members:
            * acc:
                `Vector3` of acceleration(a_x, a_y, a_z)
            * gyro:
                `Vector3` of angular speed(w_x, w_y, w_z)
        """
        def __init__(self, acc=(0, 0, 0), gyro=(0, 0, 0)):
            # ugly, I want to find something better for this
            # but I see no trivial solution that could work for a double encoder for example
            self.acc = Sensor.OutputTypes.Vector3(*acc)
            self.gyro = Sensor.OutputTypes.Vector3(*gyro)


class LSM6(AccGyro):
    """
    The LSM6 is a sensor combining an accelerometer and a gyroscope.

    The address should be 0x6A or 0x6B depending on the SDO/SA0 connection for
    the Sigi robot.

    `RawData` is `(Vector3, Vector3)`
    """

    class Regs(enum.Enum):
        CTRL1_XL = 0x10
        CTRL2_G = 0x11
        CTRL3_C = 0x12
        OUTX_L_G = 0x22
        OUTX_L_XL = 0x28

    def __init__(self, slave_addr: int = 0x6B):
        """
        The LSM6 is a sensor combining an accelerometer and a gyroscope.

        The address should be 0x6A or 0x6B depending on the SDO/SA0 connection for
        the Sigi robot.
        """
        super().__init__()
        self.interface = interface.SMBusInterface(slave_addr)
        self.interface.send_command(LSM6.Regs.CTRL1_XL, 0x50) # 208 Hz ODR, 2 g FS
        self.interface.send_command(LSM6.Regs.CTRL2_G, 0x58) # 208 Hz ODR, 1000 dps FS
        self.interface.send_command(LSM6.Regs.CTRL3_C, 0x04) # auto increment address

    def read(self):
        gyro = self.interface.read(address=LSM6.Regs.OUTX_L_G, max_bytes=6)
        acc = self.interface.read(address=LSM6.Regs.OUTX_L_XL, max_bytes=6)

        return LSM6.RawData(*struct.unpack('hhh', bytes(acc)), *struct.unpack('hhh', bytes(gyro)))


class DummyAccGyro(AccGyro):
    """
    Random values and a sine for acc
    """
    def __init__(self):
        super().__init__()
        self.t = 1

    def read(self):
        self.t+=1
        return AccGyro.RawData(acc=(random.random()-0.5, 7+math.cos(self.t/100)+random.random()*0.1-0.05, 4*math.sin(self.t/100)+random.random()*0.1-0.05), gyro=(6+random.random()*0.01-0.005, random.random()*0.01-0.005, 2+random.random()*0.01-0.005))
