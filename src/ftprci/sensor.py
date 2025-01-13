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
        def __repr__(self):
            return f"{self.__class__.__name__}({', '.join([f'{key}={value}' for key, value in self.__dict__.items()])})"


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
    class RawData(Sensor.RawData):
        def __init__(self, acc=(0, 0, 0)):
            self.acc = Sensor.OutputTypes.Vector3(*acc)


class Gyrometer(Sensor):
    class RawData(Sensor.RawData):
        def __init__(self, pqr=(0, 0, 0)):
            self.pqr = Sensor.OutputTypes.Vector3(*pqr)


class Encoder(Sensor):
    class RawData(Sensor.RawData):
        def __init__(self, turns):
            self.turns = turns

class Magnetometer(Sensor):
    class RawData(Sensor.RawData):
        def __init__(self, field=(0, 0, 0)):
            self.field = Sensor.OutputTypes.Vector3(*field)


class AccGyro(Accelerometer, Gyrometer):
    """
    Class for one-board dual sensors containing an accelerometer and a gyroscope. (6-DOF IMU)

    Example: LSM6

    `RawData` is `(Vector3, Vector3)`
    """
    class RawData(Sensor.RawData):
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
    class RawData(Sensor.RawData):
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

    class RegsAccGyro:
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
        CTRL_REG2_G = 0x11 # 00010001 00000000 r/w          Angular rate sensor Control Register 2
        CTRL_REG3_G = 0x12 # 00010010 00000000 r/w          Angular rate sensor Control Register 3
        ORIENT_CFG_G = 0x13 # 00010011 00000000 r/w         Angular rate sensor sign and orientation register
        INT_GEN_SRC_G = 0x14 # 00010100 output r            Angular rate sensor interrupt source register
        OUT_TEMP_L = 0x15 # 00010101 output r               Temperature data output register. L and H registers together express a 16-bit word in two’s complement right-justified
        OUT_TEMP_H = 0x16 # 00010110 output r
        STATUS_REG_L = 0x17 # 00010111 output r             Status register
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
        STATUS_REG_H = 0x27 # 00100111 output r             Status register
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


        class CtrlReg1:
            """
            Control register number 3 for the accelerometer and gyroscope.

            Used for enabling low power mode and for the configuration of the high pass filter.
            """
            class AccGyroOutputDataRate(enum.Enum):
                """
                Output data rate of the gyroscope and of the accelerometer if not in accelerometer only mode(see Operating modes of doc).
                """
                POWER_DOWN = 0b000
                F_14Hz9 = 0b001
                F_59Hz5 = 0b010
                F_119Hz = 0b011
                F_238Hz = 0b100
                F_476Hz = 0b101
                F_952Hz = 0b110


            class GyroFullScaleSelector(enum.Enum):
                F_245dps = 0b00
                F_500dps = 0b01
                F_2000dps = 0b11


            class GyroBandwidthSelector(enum.Enum):     # TODO
                """
                Use not understood, use BW_0, it should work
                ODR_G [2:0] BW_G [1:0] ODR [Hz] Cutoff [Hz] (1)
                1. Values in the table are indicative and can vary proportionally with the specific ODR value.
                000 00 Power-down n.a.
                000 01 Power-down n.a.
                000 10 Power-down n.a.
                000 11 Power-down n.a.
                001 00 14.9 n.a.
                001 01 14.9 n.a.
                001 10 14.9 n.a.
                001 11 14.9 n.a.
                010 00 59.5 16
                010 01 59.5 16
                010 10 59.5 16
                010 11 59.5 16
                011 00 119 14
                011 01 119 31
                011 10 119 31
                011 11 119 31
                100 00 238 14
                100 01 238 29
                100 10 238 63
                100 11 238 78
                101 00 476 21
                101 01 476 28
                101 10 476 57
                101 11 476 100
                110 00 952 33
                110 01 952 40
                110 10 952 58
                110 11 952 100
                111 00 n.a. n.a.
                111 01 n.a. n.a.
                111 10 n.a. n.a.
                111 11 n.a. n.a.
                """
                BW_0 = 0b00
                BW_1 = 0b01
                BW_2 = 0b10
                BW_3 = 0b11

            def __init__(self, odr: AccGyroOutputDataRate = AccGyroOutputDataRate.F_119Hz, fs: GyroFullScaleSelector = GyroFullScaleSelector.F_2000dps, bw: GyroBandwidthSelector = GyroBandwidthSelector.BW_0):
                self.odr = odr
                self.fs = fs
                self.bw = bw

            def __int__(self):
                return (self.odr.value<<5) + (self.fs.value<<3)+self.bw.value


        class CtrlReg2:
            """
            Control register number 3 for the accelerometer and gyroscope.

            Used for enabling low power mode and for the configuration of the high pass filter.
            """
            def __init__(self, int_sel: int = 0, out_sel: int = 0): # TODO
                self.int_sel = int_sel
                self.out_sel = out_sel

            def __int__(self):
                return (self.int_sel<<2) + self.out_sel


        class CtrlReg3:
            """
            Control register number 3 for the accelerometer and gyroscope.

            Used for enabling low power mode and for the configuration of the high pass filter.
            """
            class AccGyroLowPowerMode(enum.Enum):
                """
                Power mode.
                """
                LP_MODE = 0b1
                NORMAL_MODE = 0b0

            class HighPassFilterConfig(enum.Enum):
                """
                If enabled, the cutoff frequency can be choosen as a function of the ODR.
                Read table 52 of doc for more details.

                The cutoff frequency can be computed approximately as cutoff = 1000 / dividing_value (DV)
                """
                NOT_ENABLED = 0b000_0000
                DV_64 = 0b100_0000
                DV_32 = 0b100_0001
                DV_16 = 0b100_0010
                DV_8 = 0b100_0011
                DV_4 = 0b100_0100
                DV_2 = 0b100_0101
                DV_1 = 0b100_0110
                DV_1_OVER_2 = 0b100_0111
                DV_1_OVER_5 = 0b100_1000
                DV_1_OVER_10 = 0b100_1001

            def __init__(self, low_power: AccGyroLowPowerMode = AccGyroLowPowerMode.NORMAL_MODE, high_pass_filter: HighPassFilterConfig = HighPassFilterConfig.NOT_ENABLED):
                self.low_power = low_power
                self.high_pass_filter = high_pass_filter

            def __int__(self):
                return (self.low_power.value<<7) + self.high_pass_filter.value


        class CtrlReg4:
            """
            Control register number 4 for the accelerometer and gyroscope.

            Used for enabling each gyroscope axis output separately and to config a few params of the acc-only interrupts.
            """
            class GyroAxisOutput(enum.Enum):
                """
                Enable or disable the output of each gyro axis.
                
                Use bitwise or if necessary.
                """
                X_ENABLED = 0b001
                Y_ENABLED = 0b010
                Z_ENABLED = 0b100
                ALL_ENABLED = 0b111

            class AccLatchedInterrupt(enum.Enum):
                """
                Enable or disable latched interrupt for the accelerometer.
                """
                LATCHED = 0b1
                NOT_LATCHED = 0b0

            class AccInterruptPositionRecognitionMode(enum.Enum):
                """
                No idea what this means.
                """
                MODE_4D = 0b1
                MODE_6D = 0b0
            
            def __init__(self, gyro_axis: GyroAxisOutput = GyroAxisOutput.ALL_ENABLED, acc_latched_interrupt: AccLatchedInterrupt = AccLatchedInterrupt.NOT_LATCHED, acc_interrupt_position_recognition: AccInterruptPositionRecognitionMode = AccInterruptPositionRecognitionMode.MODE_6D):
                self.gyro_axis = gyro_axis
                self.acc_latched_interrupt = acc_latched_interrupt
                self.acc_interrupt_position_recognition = acc_interrupt_position_recognition

            def __int__(self):
                return (self.gyro_axis.value<<3)+(self.acc_latched_interrupt.value<<1)+self.acc_interrupt_position_recognition.value


        class CtrlReg5:
            """
            Control register number 5 for the accelerometer.

            Used for enabling each accelerometer axis output separately and to change decimation.
            """
            class DecimationRatio(enum.Enum):
                """
                Change the decimation (update rate, for fifo for example)
                
                A ratio of one (no decimation) means the buffer is updated after every measure.
                A ratio of two means the buffer is updated after every two measures.
                """

                ONE = 0b00
                TWO = 0b01
                FOUR = 0b10
                EIGHT = 0b11

            class AccAxisOutput(enum.Enum):
                """
                Enable or disable the output of each accelerometer axis.
                
                Use bitwise or if necessary.
                """
                X_ENABLED = 0b001
                Y_ENABLED = 0b010
                Z_ENABLED = 0b100
                ALL_ENABLED = 0b111


            def __init__(self, decimation: DecimationRatio = DecimationRatio.ONE, acc_axis: AccAxisOutput = AccAxisOutput.ALL_ENABLED):
                self.decimation = decimation
                self.acc_axis = acc_axis

            def __int__(self):
                return (self.decimation.value<<6 )+(self.acc_axis.value<<3)
        


        class CtrlReg6:
            """
            Control register number 6 for the accelerometer.

            Used to change output data rate of the accelerometer, the full scale and the bandwidth.
            """
            class AccOutputDataRate(enum.Enum):
                POWER_DOWN = 0b000
                F_10Hz = 0b001
                F_50Hz = 0b010
                F_119Hz = 0b011
                F_238Hz = 0b100
                F_476Hz = 0b101
                F_952Hz = 0b110

            class AccFullScaleSelector(enum.Enum):
                """
                Edit the full scale of the accelerometer.

                This value is in g, and is the absolute value of the maximum acceleration that can be measured(so the range is twice this value).
                """
                FS_2G = 0b00
                FS_4G = 0b10
                FS_8G = 0b11
                FS_16G = 0b01

            class AccBandwidthSelector(enum.Enum):
                """
                Anti-aliasing filter bandwidth selection.

                If unset, the value will depend on the ODR:
                    * BW = 408 Hz when ODR = 952 Hz, 50 Hz, 10 Hz
                    * BW = 211 Hz when ODR = 476 Hz
                    * BW = 105 Hz when ODR = 238 Hz
                    * BW = 50 Hz when ODR = 119 Hz
                """
                UNSET = 0b000
                F_50Hz = 0b111
                F_105Hz = 0b110
                F_211Hz = 0b101
                F_408Hz = 0b100


            def __init__(self, acc_odr: AccOutputDataRate = AccOutputDataRate.F_119Hz, acc_full_scale:AccFullScaleSelector = AccFullScaleSelector.FS_8G, bdw:AccBandwidthSelector = AccBandwidthSelector.UNSET):
                self.acc_odr = acc_odr
                self.acc_full_scale = acc_full_scale
                self.bdw = bdw

            def __int__(self):
                return (self.acc_odr.value<<5 )+(self.acc_full_scale.value<<3)+self.bdw.value

        class CtrlReg7:
            """
            Control register number 7 for the accelerometer.

            For various settings of the filters.
            """
            class HighResolution(enum.Enum):
                """
                Enable high resolution mode and filtering of the acc output. Cutoff frequency is based on ODR.
                """
                OFF = 0b000
                ODR_OVER_9 = 0b110
                ODR_OVER_50 = 0b100
                ODR_OVER_100 = 0b101
                ODR_OVER_400 = 0b111

            class FilteredDataSelection(enum.Enum):
                """
                Enable or bypass the filter.
                """
                BYPASS = 0b0
                ENABLED = 0b1

            class InterruptGeneratorHighPassFilter(enum.Enum):
                """
                Enable or bypass the filter for the interrupt generator.
                """
                DISABLED = 0b0
                ENABLED = 0b1


            def __init__(self, hi_res: HighResolution = HighResolution.OFF, data_sel:FilteredDataSelection = FilteredDataSelection.BYPASS, int_gen_filter:InterruptGeneratorHighPassFilter = InterruptGeneratorHighPassFilter.DISABLED):
                self.hi_res = hi_res
                self.data_sel = data_sel
                self.int_gen_filter = int_gen_filter

            def __int__(self):
                return (self.hi_res.value<<5 )+(self.data_sel.value<<2)+self.int_gen_filter.value

        class CtrlReg8:
            """
            Control register number 8 for the accelerometer.

            Used for various setup settings.
            """
            class RebootMemory(enum.Enum):
                """
                Reboot memory or not.

                I don't know this resets it tho...
                """
                DO_NOTHING = 0b0
                REBOOT = 0b1

            class BlockDataUpdate(enum.Enum):
                """
                Enable or disable block data update.
                """
                CONTINUOUS_UPDATE = 0b0
                BLOCK_DATA_UPDATE = 0b1

            class InterruptActivationLevel(enum.Enum):
                """
                Change the interrupt activation level.
                """
                HIGH = 0b0
                LOW = 0b1

            class PushPullOpenDrain(enum.Enum):
                """
                Change the output type of the interrupt pin.
                """
                PUSH_PULL = 0b0
                OPEN_DRAIN = 0b1

            class SPIInterfaceSelection(enum.Enum):
                """
                Change the SPI interface selection.
                """
                SPI_4_WIRE = 0b0
                SPI_3_WIRE = 0b1

            class AutomaticIncrement(enum.Enum):
                """
                Enable or disable automatic increment of the address for multiple reads.
                """
                ENABLED = 0b1
                DISABLED = 0b0

            class Endianness(enum.Enum):
                """
                Change the endianness of the output.

                Changing this won't update the sensor output computation method, so use carefully.
                """
                LITTLE_ENDIAN = 0b0
                BIG_ENDIAN = 0b1

            class SoftwareReset(enum.Enum):
                """
                Reset software.
                """
                DO_NOTHING = 0b0
                RESET = 0b0

            def __init__(self, mem_rbt: RebootMemory = RebootMemory.DO_NOTHING, bdu: BlockDataUpdate = BlockDataUpdate.CONTINUOUS_UPDATE, int_lvl:InterruptActivationLevel = InterruptActivationLevel.HIGH, pp_od:PushPullOpenDrain = PushPullOpenDrain.PUSH_PULL, spi:SPIInterfaceSelection = SPIInterfaceSelection.SPI_4_WIRE, inc:AutomaticIncrement = AutomaticIncrement.ENABLED, endianness:Endianness = Endianness.LITTLE_ENDIAN, sw_reset:SoftwareReset = SoftwareReset.DO_NOTHING):
                self.mem_rbt = mem_rbt
                self.bdu = bdu
                self.int_lvl = int_lvl
                self.pp_od = pp_od
                self.spi = spi
                self.inc = inc
                self.endianness = endianness
                self.sw_reset = sw_reset

            def __int__(self):
                return (self.mem_rbt.value<<7 )+(self.bdu.value<<6)+(self.int_lvl.value<<5)+(self.pp_od.value<<4 )+(self.spi.value<<3)+(self.inc.value<<2)+(self.endianness.value<<1 )+(self.sw_reset.value<<0)


        class CtrlReg9:
            """
            Control register number 9.

            Used for sleep mode, fifo settings, and to disable i2c connection(you normally don't do this).
            """
            class SleepMode(enum.Enum):
                """
                Gyroscope sleep mode.
                """
                DISABLED = 0b0
                ENABLED = 0b1

            class TemperatureFIFO(enum.Enum):
                """
                Put temperature in the fifo.
                """
                TEMP_NOT_IN_FIFO = 0b0
                TEMP_IN_FIFO = 0b1

            class DataAvailable(enum.Enum):
                """
                Enable or disable the data available timer.
                """
                DISABLED = 0b0
                ENABLED = 0b1

            class PushPullOpenDrain(enum.Enum):
                """
                Change the output type of the interrupt pin.
                """
                PUSH_PULL = 0b0
                OPEN_DRAIN = 0b1

            class SPIInterfaceSelection(enum.Enum):
                """
                Change the SPI interface selection.
                """
                SPI_4_WIRE = 0b0
                SPI_3_WIRE = 0b1

            class AutomaticIncrement(enum.Enum):
                """
                Enable or disable automatic increment of the address for multiple reads.
                """
                ENABLED = 0b1
                DISABLED = 0b0

            class Endianness(enum.Enum):
                """
                Change the endianness of the output.

                Changing this won't update the sensor output computation method, so use carefully.
                """
                LITTLE_ENDIAN = 0b0
                BIG_ENDIAN = 0b1

            class SoftwareReset(enum.Enum):
                """
                Reset software.
                """
                DO_NOTHING = 0b0
                RESET = 0b0

            # def __init__(self, mem_rbt: RebootMemory = RebootMemory.DO_NOTHING, bdu: BlockDataUpdate = BlockDataUpdate.CONTINUOUS_UPDATE, int_lvl:InterruptActivationLevel = InterruptActivationLevel.HIGH, pp_od:PushPullOpenDrain = PushPullOpenDrain.PUSH_PULL, spi:SPIInterfaceSelection = SPIInterfaceSelection.SPI_4_WIRE, inc:AutomaticIncrement = AutomaticIncrement.ENABLED, endianness:Endianness = Endianness.LITTLE_ENDIAN, sw_reset:SoftwareReset = SoftwareReset.DO_NOTHING):
            #     self.mem_rbt = mem_rbt
            #     self.bdu = bdu
            #     self.int_lvl = int_lvl
            #     self.pp_od = pp_od
            #     self.spi = spi
            #     self.inc = inc
            #     self.endianness = endianness
            #     self.sw_reset = sw_reset

            # def __int__(self):
            #     return (self.mem_rbt.value<<7 )+(self.bdu.value<<6)+(self.int_lvl.value<<5)+(self.pp_od.value<<4 )+(self.spi.value<<3)+(self.inc.value<<2)+(self.endianness.value<<1 )+(self.sw_reset.value<<0)



# TODO ORIENT_CFG_G and interrupt config registers


    def __init__(self, pin_SA0: int = 0):
        """
        The LSM9DS1 is a sensor combining an accelerometer, a gyroscope and a magnetometer.

        Depending on the state of the SA0 pin, the write address can be either 0xD4 or 0xD6(read is +1) for the acc and gyro, and 0x38 or 0x3C for the mag.
        """
        super().__init__()
        self.accgyro = interface.SMBusInterface(0x6A+pin_SA0)
        self.mag = interface.SMBusInterface(0x1c+pin_SA0*2)
        self.full_settings()

        # self.interface.send_command(0x50, address=LSM9DS1.RegsAccGyro.CTRL1_XL, data=True) # 208 Hz ODR, 2 g FS
        # self.interface.send_command(0x58, address=LSM9DS1.RegsAccGyro.CTRL2_G, data=0b0101_0101) # 208 Hz ODR, 1000 dps FS
        # self.interface.send_command(0x00, address=LSM9DS1.RegsAccGyro.CTRL3_C, data=0b0101_0101) # auto increment address
        # self.interface.send_command(0x00, address=LSM9DS1.RegsAccGyro.CTRL4_C, data=0b0101_0101) # auto increment address
        # self.interface.send_command(0x00, address=LSM9DS1.RegsAccGyro.CTRL5_C, data=0b0101_0101) # auto increment address

    def full_settings(self, reg1: RegsAccGyro.CtrlReg1 = None, reg2: RegsAccGyro.CtrlReg2 = None, reg3: RegsAccGyro.CtrlReg3 = None, reg4: RegsAccGyro.CtrlReg4 = None, reg5: RegsAccGyro.CtrlReg5 = None, reg6: RegsAccGyro.CtrlReg6 = None, reg7: RegsAccGyro.CtrlReg7 = None, reg8: RegsAccGyro.CtrlReg8 = None):#, reg9: RegsAccGyro.CtrlReg9 = None, reg10: RegsAccGyro.CtrlReg10 = None):
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.ACT_THS, data=True)
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.ACT_DUR, data=True)
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_CFG_XL, data=True)
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_THS_X_XL, data=True)
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_THS_Y_XL, data=True)
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_THS_Z_XL, data=True)
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL, data=True)
        self.accgyro.send_command(int(reg6) if reg6 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg6()),address=LSM9DS1.RegsAccGyro.CTRL_REG6_XL, data=True)
        self.accgyro.send_command(int(reg1) if reg1 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg1()), address=LSM9DS1.RegsAccGyro.CTRL_REG1_G, data=True)
        self.accgyro.send_command(int(reg2) if reg2 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg2()), address=LSM9DS1.RegsAccGyro.CTRL_REG2_G, data=True)
        self.accgyro.send_command(int(reg3) if reg3 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg3()),address=LSM9DS1.RegsAccGyro.CTRL_REG3_G, data=True)
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.ORIENT_CFG_G, data=True)
        self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_SRC_G, data=True)
        self.accgyro.send_command(int(reg4) if reg4 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg4()),address=LSM9DS1.RegsAccGyro.CTRL_REG4, data=True)
        self.accgyro.send_command(int(reg5) if reg5 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg5()),address=LSM9DS1.RegsAccGyro.CTRL_REG5_XL, data=True)
        self.accgyro.send_command(int(reg6) if reg6 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg6()),address=LSM9DS1.RegsAccGyro.CTRL_REG6_XL, data=True)
        self.accgyro.send_command(int(reg7) if reg7 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg7()),address=LSM9DS1.RegsAccGyro.CTRL_REG7_XL, data=True)
        self.accgyro.send_command(int(reg8) if reg8 is not None else int(LSM9DS1.RegsAccGyro.CtrlReg8()),address=LSM9DS1.RegsAccGyro.CTRL_REG8, data=True)
        # self.accgyro_writer.send_command(int(reg7),address=LSM9DS1.RegsAccGyro.CTRL_REG7_XL, data=True)
        # self.accgyro_writer.send_command(int(reg8),address=LSM9DS1.RegsAccGyro.CTRL_REG8, data=True)
        # self.accgyro_writer.send_command(int(reg9),address=LSM9DS1.RegsAccGyro.CTRL_REG9, data=True)
        # self.accgyro_writer.send_command(int(reg10),address=LSM9DS1.RegsAccGyro.CTRL_REG10, data=True)
        # self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL, data=True)
        # self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL, data=True)
        # self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL, data=True)
        # self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL, data=True)
        # self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL, data=True)
        # self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL, data=True)
        # self.accgyro.send_command(0x00, address=LSM9DS1.RegsAccGyro.INT_GEN_DUR_XL, data=True)


    def check(self):
        sensor_identity = self.accgyro.read(address=LSM9DS1.RegsAccGyro.WHO_AM_I, max_bytes=1)[0]
        status_l = self.accgyro.read(address=LSM9DS1.RegsAccGyro.STATUS_REG_L, max_bytes=1)[0]
        status_h = self.accgyro.read(address=LSM9DS1.RegsAccGyro.STATUS_REG_H, max_bytes=1)[0]
        print(f"checked sensor {sensor_identity:08b}, got status {status_l:08b} and {status_h:08b}")
        # TODO nice print of status & check of values


    def read(self):
        gyro = self.accgyro.read(address=LSM9DS1.RegsAccGyro.OUT_X_L_G, max_bytes=6)
        acc = self.accgyro.read(address=LSM9DS1.RegsAccGyro.OUT_X_L_XL, max_bytes=6)

        # mag = self.mag_reader.read(address=0x28, max_bytes=6)
        return LSM9DS1.RawData(acc=struct.unpack('hhh', bytes(acc)), pqr=struct.unpack('hhh', bytes(gyro)), field=(0, 0, 0)) #*struct.unpack('hh', bytes(mag)))
    
    def get_temp(self):
        temp = self.accgyro.read(address=LSM9DS1.RegsAccGyro.OUT_TEMP_L, max_bytes=2)
        return struct.unpack('h', bytes(temp))[0]/16

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
