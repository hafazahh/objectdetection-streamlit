"""Measure real memory footprint of the app's runtime stack (step 3: RAM budget check).

Reads RSS from /proc/self/status — no psutil dependency needed.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def rss_mb():
    with open('/proc/self/status') as f:
        for line in f:
            if line.startswith('VmRSS:'):
                return int(line.split()[1]) / 1024
    return -1


def peak_mb():
    with open('/proc/self/status') as f:
        for line in f:
            if line.startswith('VmHWM:'):
                return int(line.split()[1]) / 1024
    return -1


def mark(label):
    print(f"  RSS {rss_mb():7.1f} MB | peak {peak_mb():7.1f} MB  <- {label}", flush=True)


print('=' * 70)
print('MEMORY BUDGET MEASUREMENT (Streamlit Cloud free tier: 690MB - 2.7GB)')
print('=' * 70)

mark('bare interpreter')

import cv2
mark('+ opencv')

import numpy as np
mark('+ numpy')

import torch
mark('+ torch')

import easyocr
mark('+ easyocr (module)')

reader = easyocr.Reader(['en'], gpu=False)
mark('+ EasyOCR Reader built (models loaded)')

# Simulate one detection pass: build a plate-like image and OCR it
img = np.full((120, 400, 3), 255, dtype=np.uint8)
cv2.putText(img, 'B1234ABC', (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (0, 0, 0), 5)
mark('+ test image built')

res = reader.readtext(img, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ')
mark(f'+ one readtext pass (results={len(res)})')

print()
print('=' * 70)
print('SUMMARY')
print('=' * 70)
base = rss_mb()
print(f'  Current RSS after full stack + 1 OCR pass : {base:.1f} MB')
print(f'  Peak RSS                                  : {peak_mb():.1f} MB')
print()
print('  Streamlit Cloud free tier headroom        : 690 - 2700 MB')
if peak_mb() < 690:
    print(f'  Headroom vs 690MB floor                   : ~{690 - peak_mb():.0f} MB')
else:
    print('  WARNING: already above the 690MB floor')
print()
print('  NOTE: ultralytics/YOLO not installed — the real YOLO cost')
print('        (~+250-400MB for torch already loaded + ~50MB model)')
print('        must be measured after installing ultralytics.')
print('=' * 70)
