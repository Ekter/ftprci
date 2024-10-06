import json
import platform
import time

if not platform.platform().startswith("MicroPython"):
    MP = False
    import matplotlib.pyplot as plt
    import numpy as np
    from tqdm import tqdm

    from src.ftprci.low_level import sleep

    clock = lambda: time.perf_counter() * 1000
else:
    MP = True
    from src.ftprci.low_level import sleep, sleep_perf

    clock = lambda: time.ticks_us() / 1000

l = []

STEP = 10
N = 50

for i in range(STEP * N) if MP else tqdm(range(STEP * N)):
    script_start_time = clock()
    time.sleep(int(i / N) / 1_000)
    time_now = clock()
    elapsed_time = time_now - script_start_time
    # print(f"[{elapsed_time:.6f}] time.sleep")

    script_start_time = clock()
    sleep(int(i / N) / 1_000)
    time_now = clock()
    elapsed_time2 = time_now - script_start_time
    # print(f"[{elapsed_time2:.6f}] custom sleep")

    if MP:
        print(i)
        script_start_time = clock()
        sleep_perf(int(i / N) / 1_000)
        time_now = clock()
        elapsed_time3 = time_now - script_start_time
        # print(f"[{elapsed_time2:.6f}] custom sleep")
        l.append([elapsed_time, elapsed_time2, elapsed_time3, int(i / N)])

    else:
        l.append([elapsed_time, elapsed_time2, int(i / 50)])
if MP:
    print("copy this or open result.json")

print(l)
#json.dump(l, "result.json")
with open("result.json", "w") as res:
    res.write(json.dumps(l))

if MP:
    1 / 0

res = True
if res:
    import result
    l = result.l

plt.plot(np.array(l)[:, 0], "b.", label="time.sleep")
plt.plot(np.array(l)[:, 1], "r+", label="custom sleep")
plt.plot(np.array(l)[:, 2], "g-", label="time")
_stat = lambda x: f"{np.mean(x)=}, {np.std(x)=}"

print(_stat(np.array(l)[:, 0] - np.array(l)[:, 2]))
print(_stat(np.array(l)[:, 1] - np.array(l)[:, 2]))


plt.legend()
plt.show()

plt.plot(np.array(l)[100:200, 0], "b.", label="time.sleep")
plt.plot(np.array(l)[100:200, 1], "r+", label="custom sleep")
plt.plot(np.array(l)[100:200, 2], "g-", label="time")


print(_stat(np.array(l)[100:200, 0] - np.array(l)[100:200, 2]))
print(_stat(np.array(l)[100:200, 1] - np.array(l)[100:200, 2]))

plt.legend()
plt.show()
