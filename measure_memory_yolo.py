"""Phase 11.1 — Measure real RAM of the YOLO + Tesseract stack.

Reads RSS/VmHWM from /proc/self/status. Compares against the old EasyOCR stack
(peak 1253 MB) and the Streamlit Cloud floor (690 MB).
"""
import os
import sys

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


print('=' * 72)
print('PHASE 11.1 — MEMORY: YOLO + Tesseract stack')
print('=' * 72)

mark('bare interpreter')

import numpy as np
mark('+ numpy')

import cv2
mark('+ opencv')

import torch
mark('+ torch')

from ultralytics import YOLO
mark('+ ultralytics (module)')

import pytesseract
mark('+ pytesseract (module)')

MODEL = os.path.join(HERE, 'models', 'plate_yolov8.pt')
print(f'  model path: {MODEL}')
print(f'  model exists: {os.path.exists(MODEL)}')
print(f'  model size: {os.path.getsize(MODEL) / 1024 / 1024:.1f} MB')

model = YOLO(MODEL)
mark('+ YOLO model loaded')

# Synthetic plate-like scene
img = np.full((480, 640, 3), 90, dtype=np.uint8)
cv2.rectangle(img, (180, 300), (460, 380), (245, 245, 245), -1)
cv2.putText(img, 'B 1234 ABC', (195, 355), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (10, 10, 10), 3)
mark('+ test image built')

res = model.predict(img, conf=0.25, verbose=False)
n_boxes = len(res[0].boxes) if res and res[0].boxes is not None else 0
mark(f'+ 1 YOLO inference (boxes={n_boxes})')

# Tesseract on a cropped ROI
roi = img[300:380, 180:460]
txt = pytesseract.image_to_string(roi, config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ')
mark(f'+ 1 Tesseract pass (text={txt.strip()!r})')

print()
print('=' * 72)
print('SUMMARY')
print('=' * 72)
print(f'  Final RSS  : {rss_mb():.1f} MB')
print(f'  Peak RSS   : {peak_mb():.1f} MB')
print()
print('  OLD stack (EasyOCR) peak  : 1253.0 MB')
print(f'  NEW stack peak            : {peak_mb():.1f} MB')
delta = 1253.0 - peak_mb()
print(f'  Savings                   : {delta:+.1f} MB')
print()
print('  Streamlit Cloud floor     : 690 MB')
if peak_mb() < 690:
    print(f'  Headroom vs floor         : ~{690 - peak_mb():.0f} MB  -> FITS')
elif peak_mb() < 1500:
    print(f'  Above 690MB floor by      : {peak_mb() - 690:.0f} MB (app ran at 1253MB before, so OK)')
else:
    print('  WARNING: higher than the old stack')
print('=' * 72)
