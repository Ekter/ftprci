import platform
import time

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
        def __init__(self, th: "RunnerThread") -> None:
            self.th = th
            self.calling_queue = []

        def __or__(self, fn):
            self.calling_queue.append(fn)
            return self

        def __iter__(self):
            for call in self.calling_queue:
                yield call

        def __len__(self):
            return len(self.calling_queue)

    def __init__(self, period: float = -1):
        self.callback = RunnerThread.CallQueue(self)
        if PLATFORM == "MicroPython":
            self.thread = threading.start_new_thread(self._run, ())
        else:
            self.thread = threading.Thread(target=self._run)
            self.thread.start()
        self.period = period

    def _run(self):
        print(len(self.callback))
        a=[]
        for call in self.callback:
            a = [call(*a)]


th = RunnerThread(-1)


def f1():
    print("1")
    return 2



def f2(u):
    print(2*u)
    return 2*u


def f3(k):
    print(k)


time.sleep(1)
th.callback | f1 | f2 | f2 | f3
print("end")
th._run()
