#!/usr/bin/env python3
"""
capture_photo_imu.py

Takes a photo and reads the LSM6DSO32 IMU together on each interval, logging
everything (filename, timestamp, accel, gyro, temp) to one CSV. When capture
stops, it plots the IMU values over time with a marker at every timestamp a
photo was taken.

Run on the Pi with:
    sudo python3 capture_photo_imu.py

Options:
    --interval SECONDS   seconds between photo+IMU samples (default 1.0)
    --duration SECONDS   total seconds to capture for (default 120)
    --outdir DIR         directory to save photos + CSV + graph (default capture)

To regenerate the graph from an existing log without recapturing:
    python3 capture_photo_imu.py --analyze-only --outdir capture
"""

import argparse
import csv
import math
import os
import time
import traceback

G = 9.80665
LOG_NAME = 'capture_log.csv'
GRAPH_NAME = 'imu_graph.png'


def init_camera(still_size=(1920, 1080)):
    try:
        from picamera2 import Picamera2
    except Exception:
        print('Picamera2 not available; cannot capture images.')
        return None
    try:
        picam2 = Picamera2()
        config = picam2.create_still_configuration(main={"format": "RGB888", "size": still_size})
        picam2.configure(config)
        picam2.start()
        time.sleep(0.2)
        return picam2
    except Exception:
        print('Failed to initialize Picamera2:')
        traceback.print_exc()
        return None


def init_imu():
    try:
        import board
        from adafruit_lsm6ds.lsm6dso32 import LSM6DSO32, AccelRange
    except Exception:
        print('IMU libraries not available (board/adafruit_lsm6ds).')
        return None
    try:
        i2c = board.I2C()
        imu = LSM6DSO32(i2c)
        try:
            imu.accelerometer_range = AccelRange.RANGE_32G
            print('Set accelerometer range to 32G')
        except Exception:
            pass
        return imu
    except Exception:
        print('Failed to initialize IMU:')
        traceback.print_exc()
        return None


def capture_loop(picam2, imu, interval, duration, outdir):
    os.makedirs(outdir, exist_ok=True)
    log_path = os.path.join(outdir, LOG_NAME)

    print(f'Capturing photo+IMU to {outdir} every {interval}s for {duration}s')
    start = time.monotonic()
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['index', 'filename', 'timestamp', 'elapsed_s',
                          'accel_x', 'accel_y', 'accel_z', 'accel_mag_g',
                          'gyro_x', 'gyro_y', 'gyro_z', 'temp_c'])
        index = 0
        try:
            while True:
                loop_start = time.monotonic()
                elapsed = loop_start - start
                if elapsed >= duration:
                    break

                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f'photo_{timestamp}_{index:03d}.jpg'
                filepath = os.path.join(outdir, filename)

                try:
                    picam2.capture_file(filepath)
                    print(f'Captured {filepath}')
                except Exception:
                    print(f'Failed to capture photo {index}:')
                    traceback.print_exc()

                try:
                    accel = imu.acceleration
                    gyro = imu.gyro
                    temp = getattr(imu, 'temperature', None)
                    mag_g = math.sqrt(accel[0] ** 2 + accel[1] ** 2 + accel[2] ** 2) / G
                except Exception:
                    print('Failed to read IMU; logging blank values')
                    accel = (None, None, None)
                    gyro = (None, None, None)
                    temp = None
                    mag_g = None

                writer.writerow([index, filename, timestamp, f'{elapsed:.3f}',
                                  accel[0], accel[1], accel[2], mag_g,
                                  gyro[0], gyro[1], gyro[2], temp])
                f.flush()

                index += 1
                sleep_time = interval - (time.monotonic() - loop_start)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        except KeyboardInterrupt:
            print('Capture interrupted by user.')

    print('Capture complete. Log:', log_path)
    return log_path


def plot_log(log_path, outdir):
    import matplotlib.pyplot as plt

    elapsed = []
    accel_mag = []
    gyro_mag = []
    filenames = []

    with open(log_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['accel_mag_g']:
                continue
            elapsed.append(float(row['elapsed_s']))
            accel_mag.append(float(row['accel_mag_g']))
            gx, gy, gz = float(row['gyro_x']), float(row['gyro_y']), float(row['gyro_z'])
            gyro_mag.append(math.sqrt(gx ** 2 + gy ** 2 + gz ** 2))
            filenames.append(row['filename'])

    if len(elapsed) < 2:
        raise ValueError('Not enough logged samples to plot a graph.')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1.plot(elapsed, accel_mag, marker='o')
    ax1.set_ylabel('Accel magnitude (G)')
    ax1.set_title('IMU readings over time (marker = photo taken)')

    ax2.plot(elapsed, gyro_mag, marker='o', color='orange')
    ax2.set_ylabel('Gyro magnitude (deg/s)')
    ax2.set_xlabel('Elapsed time (s)')

    # Label every Nth photo timestamp so the axis stays readable
    step = max(1, len(elapsed) // 15)
    for i in range(0, len(elapsed), step):
        ax1.annotate(f't={elapsed[i]:.1f}s', (elapsed[i], accel_mag[i]),
                     textcoords='offset points', xytext=(0, 8), fontsize=7, rotation=45)

    fig.tight_layout()
    out_path = os.path.join(outdir, GRAPH_NAME)
    fig.savefig(out_path)
    print(f'Saved graph to {out_path}')
    return out_path


def parse_args():
    parser = argparse.ArgumentParser(description='Capture photo+IMU samples together and graph the IMU data.')
    parser.add_argument('--interval', type=float, default=1.0, help='seconds between photo+IMU samples')
    parser.add_argument('--duration', type=float, default=120.0, help='total seconds to capture for')
    parser.add_argument('--outdir', type=str, default='capture', help='directory to save photos + CSV + graph')
    parser.add_argument('--analyze-only', action='store_true',
                         help='skip capturing and just (re)plot the graph from an existing log')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.analyze_only:
        log_path = os.path.join(args.outdir, LOG_NAME)
        plot_log(log_path, args.outdir)
        return

    picam2 = init_camera()
    imu = init_imu()
    if picam2 is None or imu is None:
        print('Camera or IMU not initialized; exiting.')
        return

    try:
        log_path = capture_loop(picam2, imu, args.interval, args.duration, args.outdir)
    finally:
        try:
            picam2.stop()
        except Exception:
            pass

    try:
        plot_log(log_path, args.outdir)
    except Exception:
        print('Failed to plot graph:')
        traceback.print_exc()


if __name__ == '__main__':
    main()
