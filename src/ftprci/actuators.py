"""
Actuators class model physical actuators of the system.

They generally use Interfaces to send commands to the physical system.

One Actuator instance can be used to control as many actuators as needed, but using
separate instances is recommended for complicated systems.

Imported by main, member of the robot class.
"""

import abc
import struct
import enum
from . import interface


class Actuator(abc.ABC):
    def __init__(self, interface_command: interface.Interface):
        self.interface: interface.Interface = interface_command

    @abc.abstractmethod
    def command(self, *command):
        for comm in command:
            self.interface.send_command(comm)

    def stop(self):
        self.command(0)

    def __str__(self):
        return self.__class__.__name__

    def __call__(self, *command):
        self.command(*command)


class PololuAstar(Actuator):
    class Regs(enum.Enum):
        LEDS = 0
        MOTORS = 6
        NOTES = 24

        SLAVE_ADDRESS = 20

    def __init__(self):
        _interface = interface.SMBusInterface(PololuAstar.Regs.SLAVE_ADDRESS.value)
        super().__init__(_interface)

    def leds(self, red, yellow, green):
        self.interface.send_command(
            *struct.pack("BBB", red, yellow, green),
            address=PololuAstar.Regs.LEDS.value,
            block=True,
        )

    def play_notes(self, notes):
        raise RuntimeError("Please not.")
        self.interface.send_command(
            "B14s",
            1,
            notes.encode("ascii"),
            address=PololuAstar.Regs.NOTES.value,
            block=True,
        )

    def motors(self, left, right):
        self.interface.send_command(
            *struct.pack("hh", left, right),
            address=PololuAstar.Regs.MOTORS.value,
            block=True,
        )

    def command(self, command):
        self.motors(int(command * 80), int(command * 80))
