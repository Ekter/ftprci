from time import sleep

from pretlog import info, new_block

from src.ftprci.main import RunnerThread


def _main():
    th = RunnerThread(1)

    def f1():
        new_block()
        info(1)
        return 2

    def f2(u):
        info(2 * u)
        return 2 * u

    def f3(k):
        info(3 * k)

    info("starting")
    th >> f1 | f2 | f2 | f3
    sleep(1)
    # th._run()

    def f4(s):
        print("4")
        return s

    def f5(k):
        print(5)
        return k * 5

    def f52(k):
        print(5, 2)
        return k * 10

    def f6(*args):
        print(6)
        print(args)

    sleep(1)
    th.callback - 10
    th.callback < "a"
    th.callback | f4 | (f5, f52) | (lambda a, b: b + a) | f6
    print("----------")
    th._run()


if __name__ == "__main__":
    _main()
