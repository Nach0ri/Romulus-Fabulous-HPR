from picamera2 import Picamera2
import time
import os

# สร้าง folder เก็บรูป
os.makedirs("photos", exist_ok=True)

# เปิดกล้อง
picam2 = Picamera2()

picam2.start()

# รอให้กล้องปรับแสง
time.sleep(2)

count = 0

try:
    while True:
        filename = f"photos/photo_{count:04d}.jpg"

        picam2.capture_file(filename)

        print(f"Captured {filename}")

        count += 1

        # ถ่ายทุก 1 วินาที
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping camera")

    picam2.stop()