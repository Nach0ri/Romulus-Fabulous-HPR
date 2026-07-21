import time
import math
import csv
import subprocess
import matplotlib.pyplot as plt

import board
import busio
import adafruit_lsm6ds.lsm6dsox as lsm6ds


# ============================
# SETTINGS
# ============================

LAUNCH_THRESHOLD = 4.0   # g
LAUNCH_COUNT = 5

SAMPLE_RATE = 20         # Hz

PHOTO_INTERVAL = 1       # second


# ============================
# IMU SETUP
# ============================

i2c = busio.I2C(
    board.SCL,
    board.SDA
)

imu = lsm6ds.LSM6DSOX(i2c)


# ============================
# FILE SETUP
# ============================

start_time = time.time()

csv_name = f"flight_{int(start_time)}.csv"

csv_file = open(
    csv_name,
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


# ============================
# VARIABLES
# ============================

launch_detected = False
launch_counter = 0

photo_number = 0
last_photo_time = 0


time_data = []
g_data = []


print("Waiting for launch...")


# ============================
# MAIN LOOP
# ============================


try:

    while True:

        now = time.time()
        flight_time = now - start_time


        # Read IMU

        ax, ay, az = imu.acceleration
        gx, gy, gz = imu.gyro


        total_accel = math.sqrt(
            ax**2 +
            ay**2 +
            az**2
        )


        accel_g = total_accel / 9.81


        print(
            f"Accel: {accel_g:.2f} g"
        )


        # Save data

        writer.writerow([
            flight_time,
            accel_g,
            ax,
            ay,
            az,
            gx,
            gy,
            gz
        ])

        csv_file.flush()


        time_data.append(
            flight_time
        )

        g_data.append(
            accel_g
        )


        # =====================
        # LAUNCH DETECTION
        # =====================


        if not launch_detected:

            if accel_g > LAUNCH_THRESHOLD:
                launch_counter += 1

            else:
                launch_counter = 0


            if launch_counter >= LAUNCH_COUNT:

                launch_detected = True

                print(
                    "🚀 LAUNCH DETECTED"
                )



        # =====================
        # TAKE PHOTO
        # =====================


        if launch_detected:


            if now - last_photo_time >= PHOTO_INTERVAL:


                filename = (
                    f"photo_{int(now)}.jpg"
                )


                subprocess.run([
                    "rpicam-still",
                    "-o",
                    filename
                ])


                print(
                    "Saved:",
                    filename
                )


                last_photo_time = now



        time.sleep(
            1/SAMPLE_RATE
        )


except KeyboardInterrupt:

    print(
        "Stopping..."
    )



finally:

    csv_file.close()



# ============================
# PLOT GRAPH
# ============================

plt.figure(figsize=(10,5))

plt.plot(
    time_data,
    g_data
)

plt.xlabel(
    "Time (s)"
)

plt.ylabel(
    "Acceleration (g)"
)

plt.title(
    "Rocket Flight Acceleration"
)


plt.grid()

plt.savefig(
    "flight_plot.png"
)

plt.show()


print(
    "Finished"
)

print(
    "CSV:",
    csv_name
)

print(
    "Plot saved: flight_plot.png"
)