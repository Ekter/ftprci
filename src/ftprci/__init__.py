"""
# FTPRCI

Fast Time Python Robot Controller Interface

## Description

This library is a collection of classes and functions to help with the development
of robot controllers in Python. It is designed to be fast and easy to use, with a
focus on real-time control.
Works on CPython and MicroPython.

## Installation

To install the library, simply run:

$ pip install ftprci

in a virtual environment.

## Usage

The library is divided into several modules, each with a specific purpose:
* `interface`: Contains the `Interface` class, which is an abstract base class for
all interfaces.
* `actuators`: Contains the `Actuator` class, which is an abstract base class for
all actuators.
* `estimator`: Contains the `Estimator` class, which is an abstract base class for
all estimators.
* `controller`: Contains the `Controller` class, which is an abstract base class
for all controllers.
* `sensor`: Contains the `Sensor` class, which is an abstract base class for all
sensors.
* `logger`: Contains the `Logger` class, which is used for logging.
* `main`: Contains the `RunnerThread` class, which is used to run the controller
with precise timings.

Here is an example of how to use the library:

>>> import ftprci as fci
>>> sensor = fci.LSM6()
>>> controller = fci.PIDController() # not implemented yet :)
>>> estimator = fci.KalmanFilter()  # not implemented yet
>>> actuator = fci.DCMotor()        # not implemented yet
>>> th = fci.RunnerThread()
>>> th.callback | sensor.read | estimator.estimate | controller.steer | actuator.command
>>> th.run()

"""

from .actuators import Actuator, PololuAstar
from .controller import Controller, PIDController, LQRController, DiscreteDifferential, DiscreteIntegral
from .estimator import Estimator, LowPassFilter, HighPassFilter, ComplementaryFilter
from .interface import DummyInterface, Interface, SMBusInterface
from .main import RunnerThread
from .sensor import LSM6, Sensor, DummyAccGyro
# import .logger
