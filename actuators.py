"""
Actuators class model physical actuators of the system.

They generally use Interfaces to send commands to the physical system.

One Actuator instance can be used to control as many actuators as needed, but using
separate instances is recommended for complicated systems.

Imported by main, member of the robot class.
"""



class Actuator(BaseActuator):
    def __init__(self):
        pass

    def command(self):
        pass

    def stop():
        pass

    def __str__(self):
        return "Actuator"
