import platform
import time
from typing import Union, Callable

from actuators import Actuator

if platform.platform().startswith("MicroPython"):
    PLATFORM = "MicroPython"
    import _thread as threading
else:
    PLATFORM = platform.python_implementation()
    import threading


class Robot:
    def __init__(self) -> None:
        self.actuators: list[Actuator] = []
        self.sensors = []

    def set_actuators():
        pass


class RunnerThread:
    class CallQueue:
        def __init__(self, _th: "RunnerThread") -> None:
            self.th = _th
            self.calling_queue = []

        def __or__(self, fn: Union[tuple[Callable], Callable]):
            self.calling_queue.append((fn))
            return self

        def __iter__(self):
            """
            Iteration over the calling queue to get all methods in order

            Indirect iteration to allow for dynamic changes to the queue
            during execution
            """
            call_n = 0
            while call_n < len(self.calling_queue):
                yield self.calling_queue[call_n]
                call_n += 1

        def __len__(self):
            return len(self.calling_queue)

        def __sub__(self, fn: Union[int, tuple[Callable], Callable]):
            if isinstance(fn, int):
                self.calling_queue = self.calling_queue[:-fn]
                return self
            self.calling_queue.remove(fn)
            return self

        def __lt__(self, *args):
            self.th.initial_args = args
            return self

    def __init__(self, period: float = -1):
        self.initial_args = []
        self.callback = RunnerThread.CallQueue(self)
        if PLATFORM == "MicroPython":
            self.thread = threading.start_new_thread(self._run, ())
        else:
            self.thread = threading.Thread(target=self._run)
            self.thread.start()
        self.period = period

    def _run(self):
        print(len(self.callback))
        a = self.initial_args
        for call in self.callback:
            a = [(call_(*a) for call_ in call) if isinstance(call, tuple) else call(*a)]


th = RunnerThread(-1)


def f1():
    print(1)
    return 2


def f2(u):
    print(2)
    print(2 * u)
    return 2 * u


def f3(k):
    print(3)
    print(k)


time.sleep(1)
th.callback | f1 | f2 | f2 | f3
print("----------")
th._run()


def f4(s):
    print("4")
    return s


def f5(k):
    print(5)
    return k * 5

def f52(k):
    print("52")
    return k * 10


def f6(*args):
    print(6)
    print(args)


time.sleep(1)
th.callback - 10
th.callback < "a"
th.callback | f4 | (f5, f52) | f6
print("----------")
th._run()
