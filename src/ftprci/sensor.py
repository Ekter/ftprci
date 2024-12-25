"""
Sensor module.

This module defines the abstract class `Sensor` and some concrete sensors.

Public classes:
    * `Sensor`: Abstract base class for sensors.
    * `Accelerometer`: Sensor for acceleration.
    * `Gyrometer`: Sensor for angular speed.
    * `Encoder`: Sensor for rotations.
    * `AccGyro`: Sensor for acceleration and angular speed.
    * `LSM6`: Sensor for acceleration and angular speed.
    * `DummyAccGyro`:
        Sensor for acceleration and angular speed with somehow random but consistent values.
"""


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
        return self.read(*args)

    def __or__(self, other):
        return self, other


class Accelerometer(Sensor):
    class RawData:
        def __init__(self, acc=(0, 0, 0)):
            self.acc = Sensor.OutputTypes.Vector3(*acc)


class Gyrometer(Sensor):
    class RawData:
        def __init__(self, pqr=(0, 0, 0)):
            self.pqr = Sensor.OutputTypes.Vector3(*pqr)


class Encoder(Sensor):
    class RawData:
        def __init__(self, turns):
            self.turns = turns

class Magnetometer(Sensor):
    class RawData:
        def __init__(self, field=(0, 0, 0)):
            self.field = Sensor.OutputTypes.Vector3(*field)


class AccGyro(Accelerometer, Gyrometer):
    """
    Class for one-board dual sensors containing an accelerometer and a gyroscope. (6-DOF IMU)

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
                `Vector3` of angular speed(p, q, r)
        """
        def __init__(self, acc=(0, 0, 0), pqr=(0, 0, 0)):
            # ugly, I want to find something better for this
            # but I see no trivial solution that could work for a double encoder for example
            self.acc = Sensor.OutputTypes.Vector3(*acc)
            self.pqr = Sensor.OutputTypes.Vector3(*pqr)

class AccGyroMag(Accelerometer, Gyrometer, Magnetometer):
    """
    Class for 9-DOF IMU(accelerometer, gyroscope, and magnetometer).

    Example: LSM9DS1

    `RawData` is (Vector3, Vector3, Vector3)`
    """
    class RawData:
        """
        Class for storing the output of combined accelerometers, gyroscopes and magnetometers.

        Members:
            * acc:
                `Vector3` of acceleration(a_x, a_y, a_z)
            * gyro:
                `Vector3` of angular speed(p, q, r)
            * field:
                `Vector3` of magnetic field(x, y, z)
        """
        def __init__(self, acc=(0, 0, 0), pqr=(0, 0, 0), field=(0, 0, 0)):
            self.acc = Sensor.OutputTypes.Vector3(*acc)
            self.pqr = Sensor.OutputTypes.Vector3(*pqr)
            self.field = Sensor.OutputTypes.Vector3(*field)



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
        self.interface.send_command(0x50, address=LSM6.Regs.CTRL1_XL.value, data=True) # 208 Hz ODR, 2 g FS
        self.interface.send_command(0x58, address=LSM6.Regs.CTRL2_G.value, data=True) # 208 Hz ODR, 1000 dps FS
        self.interface.send_command(0x04, address=LSM6.Regs.CTRL3_C.value, data=True) # auto increment address

    def read(self):
        gyro = self.interface.read(address=LSM6.Regs.OUTX_L_G, max_bytes=6)
        acc = self.interface.read(address=LSM6.Regs.OUTX_L_XL, max_bytes=6)

        return LSM6.RawData(*struct.unpack('hhh', bytes(acc)), *struct.unpack('hhh', bytes(gyro)))


class LSM9DS1(AccGyroMag):
    """
    The LSM9DS1 is a sensor combining an accelerometer, a gyroscope and a magnetometer.

    See [datasheet](https://www.lcsc.com/datasheet/lcsc_datasheet_2202131700_STMicroelectronics-LSM9DS1TR_C2655096.pdf)

    `RawData` is `(Vector3, Vector3, Vector3)`
    """

    class RegsAccGyro(enum.Enum):
        "NAME = HEX # BIN DEFAULT MODE COMMENTARY"
        ACT_THS = 0x04          # 00000100 00000000 r/w     Activity threshold register
        ACT_DUR = 0x05 # 00000101 00000000 r/w              Inactivity duration register
        INT_GEN_CFG_XL = 0x06 # 00000110 00000000 r/w       Linear acceleration sensor interrupt generator configuration register
        INT_GEN_THS_X_XL = 0x07 # 00000111 00000000 r/w     Linear acceleration sensor interrupt threshold register
        INT_GEN_THS_Y_XL = 0x08 # 00001000 00000000 r/w     Linear acceleration sensor interrupt threshold register
        INT_GEN_THS_Z_XL = 0x09 # 00001001 00000000 r/w     Linear acceleration sensor interrupt threshold register
        INT_GEN_DUR_XL = 0x0A # 00001010 00000000 r/w       Linear acceleration sensor interrupt duration register
        REFERENCE_G = 0x0B # 00001011 00000000 r/w          Angular rate sensor reference value register for digital high-pass filter
        INT1_CTRL = 0x0C # 00001100 00000000 r/w            INT1_A/G pin control register
        INT2_CTRL = 0x0D # 00001101 00000000 r/w            INT2_A/G pin control register
        WHO_AM_I = 0x0F # 00001111 01101000 r               Who_AM_I register
        CTRL_REG1_G = 0x10 # 00010000 00000000 r/w          Angular rate sensor Control Register 1
        "ODR_G2 ODR_G1 ODR_G0 FS_G1 FS_G0 0 BW_G1 BW_G0"
        CTRL_REG2_G = 0x11 # 00010001 00000000 r/w          Angular rate sensor Control Register 2
        CTRL_REG3_G = 0x12 # 00010010 00000000 r/w          Angular rate sensor Control Register 3
        ORIENT_CFG_G = 0x13 # 00010011 00000000 r/w         Angular rate sensor sign and orientation register
        INT_GEN_SRC_G = 0x14 # 00010100 output r            Angular rate sensor interrupt source register
        OUT_TEMP_L = 0x15 # 00010101 output r               Temperature data output register. L and H registers together express a 16-bit word in two’s complement right-justified
        OUT_TEMP_H = 0x16 # 00010110 output r
        STATUS_REG = 0x17 # 00010111 output r               Status register
        OUT_X_L_G = 0x18 # 00011000 output r                Angular rate sensor pitch axis (X) angular rate output register. The value is expressed as a 16-bit word in two’s complement
        OUT_X_H_G = 0x19 # 00011001 output r
        OUT_Y_L_G = 0x1A # 00011010 output r                Angular rate sensor roll axis (Y) angular rate output register. The value is expressed as a 16-bit word in two’s complement
        OUT_Y_H_G = 0x1B # 00011011 output r
        OUT_Z_L_G = 0x1C # 00011100 output r                Angular rate sensor yaw axis (Z) angular rate output register. The value is expressed as a 16-bit word in two’s complement
        OUT_Z_H_G = 0x1D # 00011101 output r
        CTRL_REG4 = 0x1E # 00011110 00111000 r/w            Control register 4
        CTRL_REG5_XL = 0x1F # 00011111 00111000 r/w         Linear acceleration sensor Control Register 5
        CTRL_REG6_XL = 0x20 # 00100000 00000000 r/w         Linear acceleration sensor Control Register 6
        CTRL_REG7_XL = 0x21 # 00100001 00000000 r/w         Linear acceleration sensor Control Register 7
        CTRL_REG8 = 0x22 # 00100010 00000100 r/w            Control register 8
        CTRL_REG9 = 0x23 # 00100011 00000000 r/w            Control register 9
        CTRL_REG10 = 0x24 # 00100100 00000000 r/w           Control register 10
        INT_GEN_SRC_XL = 0x26 # 00100110 output r           Linear acceleration sensor interrupt source register
        STATUS_REG = 0x27 # 00100111 output r               Status register
        OUT_X_L_XL = 0x28 # 00101000 output r               Linear acceleration sensor X-axis output register. The value is expressed as a 16-bit word in two’s complement
        OUT_X_H_XL = 0x29 # 00101001 output r
        OUT_Y_L_XL = 0x2A # 00101010 output r               Linear acceleration sensor Y-axis output register. The value is expressed as a 16-bit word in two’s complement
        OUT_Y_H_XL = 0x2B # 00101011 output r
        OUT_Z_L_XL = 0x2C # 00101100 output r               Linear acceleration sensor Z-axis output register. The value is expressed as a 16-bit word in two’s complement
        OUT_Z_H_XL = 0x2D # 00101101 output r
        FIFO_CTRL = 0x2E # 00101110 00000000 r/w            FIFO control register
        FIFO_SRC = 0x2F # 00101111 output r                 FIFO status control register
        INT_GEN_CFG_G = 0x30 # 00110000 00000000 r/w        Angular rate sensor interrupt generator configuration register
        INT_GEN_THS_XH_G = 0x31 # 00110001 00000000 r/w     Angular rate sensor interrupt generator threshold registers. The value is expressed as a 15-bit word in two’s complement
        INT_GEN_THS_XL_G = 0x32 # 00110010 00000000 r/w
        INT_GEN_THS_YH_G = 0x33 # 00110011 00000000 r/w     Angular rate sensor interrupt generator threshold registers. The value is expressed as a 15-bit word in two’s complement
        INT_GEN_THS_YL_G = 0x34 # 00110100 00000000 r/w
        INT_GEN_THS_ZH_G = 0x35 # 00110101 00000000 r/w     Angular rate sensor interrupt generator threshold registers. The value is expressed as a 15-bit word in two’s complement
        INT_GEN_THS_ZL_G = 0x36 # 00110110 00000000 r/w
        INT_GEN_DUR_G = 0x37 # 00110111 00000000 r/w        Angular rate sensor interrupt generator duration register

    class WorkingFrequencies(enum.Enum):fgt

    def __init__(self, pin_SA0: int = 0):
        """
        The LSM9DS1 is a sensor combining an accelerometer, a gyroscope and a magnetometer.

        Depending on the state of the SA0 pin, the write address can be either 0xD4 or 0xD6(read is +1) for the acc and gyro, and 0x38 or 0x3C for the mag.
        """
        super().__init__()
        self.accgyro_writer = interface.SMBusInterface(0xD4+pin_SA0*2)
        self.accgyro_reader = interface.SMBusInterface(0xD5+pin_SA0*2)
        self.mag_reader = interface.SMBusInterface(0x38+pin_SA0*4)
        self.mag_writer = interface.SMBusInterface(0x39+pin_SA0*4)
        self.full_settings()

        self.interface.send_command(0x50, address=LSM9DS1.Regs.CTRL1_XL.value, data=True) # 208 Hz ODR, 2 g FS
        self.interface.send_command(0x58, address=LSM9DS1.Regs.CTRL2_G.value, data=0b0101_0101) # 208 Hz ODR, 1000 dps FS
        self.interface.send_command(0x00, address=LSM9DS1.Regs.CTRL3_C.value, data=0b0101_0101) # auto increment address
        self.interface.send_command(0x00, address=LSM9DS1.Regs.CTRL4_C.value, data=0b0101_0101) # auto increment address
        self.interface.send_command(0x00, address=LSM9DS1.Regs.CTRL5_C.value, data=0b0101_0101) # auto increment address

    def full_settings(self, freq):
        self.accgyro_writer.send_command(0x00, address=LSM9DS1.RegsAccGyro.ACT_THS)
        self.accgyro_writer.send_command(0x00, address=LSM9DS1.RegsAccGyro.ACT_DUR)
        self.accgyro_writer.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_CFG_XL)
        self.accgyro_writer.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_THS_X_XL)
        self.accgyro_writer.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_THS_Y_XL)
        self.accgyro_writer.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_THS_Z_XL)
        self.accgyro_writer.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL)
        self.accgyro_writer.send_command()
        

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
