import time
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from low_level import sleep


l = []

for i in tqdm(range(1000)):
    script_start_time = time.perf_counter()
    time.sleep(int(i/100)/1_000)
    time_now = time.perf_counter()
    elapsed_time = (time_now - script_start_time) * 1000
    # print(f"[{elapsed_time:.6f}] time.sleep")

    script_start_time = time.perf_counter()
    sleep(int(i/100)/1_000)
    time_now = time.perf_counter()
    elapsed_time2 = (time_now - script_start_time) * 1000
    # print(f"[{elapsed_time2:.6f}] custom sleep")
    l.append([elapsed_time, elapsed_time2, int(i/100)])

print(l)

plt.plot(np.array(l)[:, 0],"b.", label="time.sleep")
plt.plot(np.array(l)[:, 1],"r+", label="custom sleep")
plt.plot(np.array(l)[:, 2],"g-", label="time")
_stat = lambda x: f"{np.mean(x)=}, {np.std(x)=}"

print(_stat(np.array(l)[:, 0]-np.array(l)[:, 2]))
print(_stat(np.array(l)[:, 1]-np.array(l)[:, 2]))


plt.legend()
plt.show()

plt.plot(np.array(l)[100:200, 0],"b.", label="time.sleep")
plt.plot(np.array(l)[100:200, 1],"r+", label="custom sleep")
plt.plot(np.array(l)[100:200, 2],"g-", label="time")


print(_stat(np.array(l)[100:200, 0]-np.array(l)[100:200, 2]))
print(_stat(np.array(l)[100:200, 1]-np.array(l)[100:200, 2]))

plt.legend()
plt.show()
