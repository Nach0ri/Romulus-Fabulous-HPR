#!/usr/bin/env python3
"""
newscript_camera.py

Takes photos with the Pi Camera (v2.1, via Picamera2) on a fixed interval
and logs each capture (filename + timestamp) to a CSV file.

Run on the Pi with:
    sudo python3 newscript_camera.py

Options:
    --interval SECONDS   seconds between photos (default 1.0)
    --duration SECONDS   total seconds to capture for (default 120)
    --outdir DIR         directory to save photos + CSV log (default photos)
"""

import argparse
import csv
import os
import time
import traceback


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


def capture_photos(picam2, interval, duration, outdir):
    os.makedirs(outdir, exist_ok=True)
    log_path = os.path.join(outdir, 'photo_log.csv')

    print(f'Capturing photos to {outdir} every {interval}s for {duration}s')
    start = time.monotonic()
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['index', 'filename', 'timestamp', 'elapsed_s'])
        index = 0
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
                writer.writerow([index, filename, timestamp, f'{elapsed:.3f}'])
                f.flush()
            except Exception:
                print(f'Failed to capture photo {index}:')
                traceback.print_exc()

            index += 1
            sleep_time = interval - (time.monotonic() - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)

    print('Capture complete. Log:', log_path)


def parse_args():
    parser = argparse.ArgumentParser(description='Take photos on an interval and log them to CSV.')
    parser.add_argument('--interval', type=float, default=1.0, help='seconds between photos')
    parser.add_argument('--duration', type=float, default=120.0, help='total seconds to capture for')
    parser.add_argument('--outdir', type=str, default='photos', help='directory to save photos + CSV log')
    return parser.parse_args()


def main():
    args = parse_args()

    picam2 = init_camera()
    if picam2 is None:
        print('Camera not initialized; exiting.')
        return

    try:
        capture_photos(picam2, args.interval, args.duration, args.outdir)
    finally:
        try:
            picam2.stop()
        except Exception:
            pass


if __name__ == '__main__':
    main()
