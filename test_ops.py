import time
import math
import csv
import matplotlib.pyplot as plt

import board
import busio
import adafruit_lsm6ds.lsm6dsox as lsm6ds


# ==========================
# SETTINGS
# ==========================

SAMPLE_RATE = 50   # Hz
TEST_TIME = 60     # seconds


# ==========================
# IMU SETUP
# ==========================

i2c = busio.I2C(
    board.SCL,
    board.SDA
)

imu = lsm6ds.LSM6DSOX(i2c)


# ==========================
# FILE SETUP
# ==========================

filename = f"imu_test_{int(time.time())}.csv"

csv_file = open(
    filename,
    "w",
    newline=""
)

writer = csv.writer(csv_file)

writer.writerow([
    "time",
    "accel_g",
    "ax",
    "ay",
    "az",
    "gx",
    "gy",
    "gz"
])


# ==========================
# DATA STORAGE
# ==========================

time_data = []
g_data = []


print("===================")
print("IMU GROUND TEST")
print("===================")
print("Press Ctrl+C to stop")


start = time.time()


try:

    while True:

        current = time.time()

        elapsed = current - start


        # Read IMU

        ax, ay, az = imu.acceleration
        gx, gy, gz = imu.gyro


        # Calculate acceleration

        total_accel = math.sqrt(
            ax**2 +
            ay**2 +
            az**2
        )


        accel_g = total_accel / 9.81


        print(
            f"Time: {elapsed:.2f}s | "
            f"Accel: {accel_g:.3f} g"
        )


        # Save CSV

        writer.writerow([
            elapsed,
            accel_g,
            ax,
            ay,
            az,
            gx,
            gy,
            gz
        ])

        csv_file.flush()


        # Store for graph

        time_data.append(elapsed)
        g_data.append(accel_g)


        if elapsed >= TEST_TIME:
            break


        time.sleep(
            1 / SAMPLE_RATE
        )


except KeyboardInterrupt:

    print("\nStopping test...")


finally:

    csv_file.close()



# ==========================
# GRAPH
# ==========================

print("Generating graph...")


plt.figure(figsize=(10,5))

plt.plot(
    time_data,
    g_data
)


plt.xlabel(
    "Time (seconds)"
)

plt.ylabel(
    "Acceleration (g)"
)

plt.title(
    "IMU Ground Test Acceleration"
)

plt.grid()


plt.savefig(
    "imu_ground_test.png"
)


plt.show()


print("===================")
print("TEST COMPLETE")
print("CSV:", filename)
print("Graph: imu_ground_test.png")
print("===================")