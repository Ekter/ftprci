import _thread
import platform

if platform.platform().startswith("MicroPython"):
    PLATFORM = "MicroPython"
    # only esp32 and rapsberry pi pico are supported for now

    import os

    import machine

    if os.uname().sysname == "rp2":
        # only for pico
        machine.freq(240000000)  # full speed or nothing
        # doubles the accuracy of the timer approximately

    import time

    def sleep(t):
        time.sleep_us(int(t * 1e6))

    def ticks_us():
        return time.ticks_us()

    def ticks_diff(a, b):
        return time.ticks_diff(a, b)

    # because better performance like this
    # trunk-ignore(ruff/E731)
    sleep2 = lambda t: time.sleep_us(int(t * 1e6))

    def sleep_perf(t):
        begin = time.ticks_cpu()
        if t > 1e-2:
            time.sleep(t - 1e-2)
        end = begin + int(t * 1e6)
        while time.ticks_cpu() < end:
            pass

    script_start_time = time.ticks_cpu()
    time.sleep(0.001)
    time_now = time.ticks_cpu()
    elapsed_time = (time_now - script_start_time) / 1000
    print("[%.4f] time.sleep" % elapsed_time)

    script_start_time = time.ticks_cpu()
    time.sleep_us(int(0.001 * 1e6))
    time_now = time.ticks_cpu()
    elapsed_time = (time_now - script_start_time) / 1000
    print("[%.4f] time.sleep_us" % elapsed_time)

    script_start_time = time.ticks_cpu()
    sleep(0.001)
    time_now = time.ticks_cpu()
    elapsed_time = (time_now - script_start_time) / 1000
    print("[%.4f] sleep" % elapsed_time)

    script_start_time = time.ticks_cpu()
    sleep2(0.001)
    time_now = time.ticks_cpu()
    elapsed_time = (time_now - script_start_time) / 1000
    print("[%.4f] sleep lambda" % elapsed_time)

    script_start_time = time.ticks_cpu()
    sleep_perf(0.001)
    time_now = time.ticks_cpu()
    elapsed_time = (time_now - script_start_time) / 1000
    print("[%.4f] sleep_perf" % elapsed_time)

    print("")

else:
    PLATFORM = platform.python_implementation()
    import time
    from typing import Callable

    def sleep(t):
        begin = time.perf_counter_ns()
        if t > 1e-2:
            time.sleep(t - 1e-2)
        end = begin + int(t * 1e9)
        while time.perf_counter_ns() < end:
            pass

    def ticks_us():
        return time.perf_counter_ns() * 1e-3

    def ticks_diff(a, b):
        return (b - a) % 1e10


class FastBlockingTimer:
    def __init__(
        self,
        *args,
        period: float = -1,
        frequency: float = -1,
        periodic: bool = None,
        callback: Callable = None,
        **kwargs,
    ) -> None:
        self.running = False
        if period == -1 and frequency == -1 or period != -1 and frequency != -1:
            raise ValueError("Either period or frequency must be set and not both")
        if period != -1:
            self.period_us = period * 1e6
            self.periodic = False
        else:
            self.period_us = 1 / frequency * 1e6
            self.periodic = True
        if periodic is not None:
            self.periodic = periodic
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """
        Run the timer in current thread
        """
        self.running = True
        loop = 1
        beg_loop = ticks_us()
        while self.running:
            beg_us = ticks_us()
            self.callback(*self.args, **self.kwargs)
            end_us = ticks_us()
            if self.periodic:
                sleep(
                    max(ticks_diff(beg_loop + loop * self.period_us, end_us) / 1e6, 0)
                )
            else:
                duration = ticks_diff(end_us, beg_us)
                sleep(max((self.period_us - duration) / 1e6, 0))

    def stop(self):
        """must be called from another thread"""
        self.running = False
