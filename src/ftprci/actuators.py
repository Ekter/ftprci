"""
Actuators class model physical actuators of the system.

They generally use Interfaces to send commands to the physical system.

One Actuator instance can be used to control as many actuators as needed, but using
separate instances is recommended for complicated systems.

Imported by main, member of the robot class.
"""

import abc
import interface

class Actuator(abc.ABC):
    def __init__(self, interface_command: interface.Interface):
        self.interface: interface.Interface = interface_command

    @abc.abstractmethod
    def command(self, *args):
        for comm in args:
            self.interface.send_command(comm)

    def stop(self):
        self.command(0)

    def __str__(self):
        return self.__class__.__name__
