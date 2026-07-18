#!/usr/bin/env python3
"""
analyze_photos.py

Reads timestamps for a folder of captured photos and plots a graph showing
elapsed time and the interval between consecutive shots. Useful for
checking how consistent the capture rate actually was.

Timestamp source (in priority order):
    1. A `photo_log.csv` file in the photo folder (columns: filename, timestamp)
    2. Each photo file's last-modified time, if no CSV log is present

Run:
    python3 analyze_photos.py --folder photos --out photos/timing_graph.png
"""

import argparse
import csv
import os
from datetime import datetime

import matplotlib.pyplot as plt

TIMESTAMP_FORMATS = ['%Y%m%d_%H%M%S', '%Y-%m-%d %H:%M:%S']


def parse_timestamp(value):
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f'Could not parse timestamp: {value}')


def load_from_csv(csv_path):
    entries = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append((row['filename'], parse_timestamp(row['timestamp'])))
    return entries


def load_from_mtimes(folder):
    entries = []
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(folder, name)
            entries.append((name, datetime.fromtimestamp(os.path.getmtime(path))))
    entries.sort(key=lambda e: e[1])
    return entries


def load_timestamps(folder):
    csv_path = os.path.join(folder, 'photo_log.csv')
    if os.path.exists(csv_path):
        print(f'Using timestamps from {csv_path}')
        return load_from_csv(csv_path)
    print(f'No photo_log.csv found; using file modified times in {folder}')
    return load_from_mtimes(folder)


def plot_timestamps(entries, out_path):
    if len(entries) < 2:
        raise ValueError('Need at least 2 photos with timestamps to plot a graph.')

    start = entries[0][1]
    elapsed = [(ts - start).total_seconds() for _, ts in entries]
    indices = list(range(len(entries)))
    intervals = [elapsed[i] - elapsed[i - 1] for i in range(1, len(elapsed))]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

    ax1.plot(indices, elapsed, marker='o')
    ax1.set_xlabel('Photo index')
    ax1.set_ylabel('Elapsed time (s)')
    ax1.set_title('Elapsed time per photo')

    ax2.plot(indices[1:], intervals, marker='o', color='orange')
    ax2.set_xlabel('Photo index')
    ax2.set_ylabel('Interval since previous photo (s)')
    ax2.set_title('Interval between consecutive photos')

    fig.tight_layout()
    fig.savefig(out_path)
    print(f'Saved graph to {out_path}')


def parse_args():
    parser = argparse.ArgumentParser(description='Analyze photo timestamps and plot a timing graph.')
    parser.add_argument('--folder', type=str, default='photos', help='folder containing captured photos')
    parser.add_argument('--out', type=str, default=None, help='output path for the graph image')
    return parser.parse_args()


def main():
    args = parse_args()
    out_path = args.out or os.path.join(args.folder, 'timing_graph.png')

    entries = load_timestamps(args.folder)
    plot_timestamps(entries, out_path)


if __name__ == '__main__':
    main()
