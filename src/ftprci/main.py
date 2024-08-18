from .actuators import Actuator

from .low_level import sleep, FastBlockingTimer

import _thread

try:
    from typing import Callable
except Exception:
    print("micropython i guess")


class Robot:
    def __init__(self) -> None:
        self.actuators: list[Actuator] = []
        self.sensors = []

    def set_actuators(self):
        pass


class RunnerThread:
    class CallQueue:
        def __init__(self, _th: "RunnerThread") -> None:
            self.th = _th
            self.calling_queue = []

        def __or__(self, fn: tuple[Callable] | Callable):
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

        def __sub__(self, fn: int | tuple[Callable] | Callable):
            if isinstance(fn, int):
                self.calling_queue = self.calling_queue[:-fn]
                return self
            self.calling_queue.remove(fn)
            return self

        def __lt__(self, *args):
            self.th.initial_args = args
            return self

    def __init__(
        self,
        period: float = -1,
        frequency: float = -1,
        periodic: bool = None,
    ):
        self.initial_args = []
        self.callback = RunnerThread.CallQueue(self)
        self.timer = FastBlockingTimer(period=period, frequency=frequency, periodic=periodic, callback=self._run)
        self.thread = _thread.start_new_thread(self.timer.run, ())

    def _run(self):
        # print(len(self.callback))
        a = self.initial_args
        for call in self.callback:
            a = [call_(*a) for call_ in call] if isinstance(call, tuple) else [call(*a)]


def _main():
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

    sleep(1)
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
        print(52)
        return k * 10

    def f6(*args):
        print(6)
        print(args)

    sleep(1)
    th.callback - 10
    th.callback < "a"
    th.callback | f4 | (f5, f52) | (lambda a, b: b) | f6
    print("----------")
    th._run()


if __name__ == "__main__":
    _main()
