from .actuators import BaseActuator

class Robot:
    def __init__(self) -> None:
        self.actuators:list[BaseActuator] = []
        self.sensors = []


    def set_actuators()
