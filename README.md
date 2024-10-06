# FTPRCI

Fast Time Python Robot Controller Interface


## Description

This library is a collection of classes and functions to help with the development
of robot controllers in Python. It is designed to be fast and easy to use, with a
focus on real-time control.
Works on CPython and MicroPython.


## Installation

To install the library, simply run:

    ```sh
    pip install ftprci
    ```

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
* `logger`: Contains the `Logger` class, which is used for logging. # TODO
* `main`: Contains the `RunnerThread` class, which is used to run the controller
with precise timings.

Here is an example of how to use the library:

    ```python
    import ftprci as fci

    th = fci.RunnerThread()

    sensor = fci.LSM6()
    estimator = fci.KalmanFilter()
    controller = fci.PIDController(1, 10, 0.1)
    actuator = fci.DCMotor()

    th.callback | sensor.read | estimator.estimate | controller.steer | actuator.command
    th.run()
    ```


## Contributing

Do not hesitate to contribute to the project if you create a new sensor, estimator, or anything!
You can open a pull request or an issue on the GitHub repository.
