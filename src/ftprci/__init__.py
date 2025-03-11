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

in a virtual environment if possible, but ftprci shouldn't cause system conflicts.

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
* `main`: Contains the `Clock` and `RunnerThread` classes, which are used to run
loops with precise timings.

Here is an example of how to use the library:

>>> import ftprci as fci
>>> sensor = fci.LSM6()
>>> controller = fci.PIDController()
>>> estimator = fci.KalmanFilter()  # not implemented yet
>>> actuator = fci.DCMotor()        # not implemented yet
>>> th = fci.RunnerThread()
>>> th.callback | sensor.read | estimator.estimate | controller.steer | actuator.command
>>> th.run()

"""

from . import (
    actuators,
    controller,
    estimator,
    interface,
    logger,
    low_level,
    main,
    sensor,
)
from .actuators import Actuator, PololuAstar
from .controller import (
    Controller,
    DiscreteDifferential,
    DiscreteIntegral,
    LQRController,
    PIDController,
)
from .estimator import (
    ComplementaryFilter,
    DiscreteLowPassFilter,
    Estimator,
    HighPassFilter,
    LinearKalmanFilter,
)
from .interface import DummyInterface, Interface, SMBusInterface
from .logger import (
    ClockedLogger,
    ClockedMultiPlotLogger3D,
    ClockedPlotLogger1D,
    DataComparativeLogger,
    FourierClockedPlotLogger1D,
    Logger,
    PlotLogger3D,
    ProgressBar,
    TimedLogger,
    TimedPlotLogger1D,
)
from .low_level import FastBlockingTimer, sleep
from .main import Clock, RunnerThread
from .sensor import LSM6, LSM9DS1, DummyAccGyro, Sensor, Trajectory3D
