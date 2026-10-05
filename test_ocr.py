"""Synthetic plate test for OCR accuracy improvements."""
import os
import tempfile

import cv2
import numpy as np

import ocr


def make_synthetic_plate(text="B 2301 PZX", width=600, height=150):
    img = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(img, (5, 5), (width - 5, height - 5), (255, 255, 255), -1)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 2.0
    thickness = 4
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    x = (width - tw) // 2
    y = (height + th) // 2
    cv2.putText(img, text, (x, y), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)
    return img


def main():
    plate = make_synthetic_plate()
    tmp = os.path.join(tempfile.gettempdir(), "synthetic_plate.png")
    cv2.imwrite(tmp, plate)
    print(f"Saved synthetic plate to {tmp}, shape={plate.shape}")

    print("\n=== upscale_roi ===")
    upscaled = ocr.upscale_roi(plate)
    print(f"upscaled shape: {upscaled.shape}")

    print("\n=== generate_variants ===")
    variants = ocr.generate_variants(upscaled)
    for name, v in variants.items():
        print(f"  {name}: shape={v.shape}")

    print("\n=== ocr_plate (full synthetic plate) ===")
    results = ocr.ocr_plate(plate)
    for text, conf in results:
        print(f"  text={text!r} conf={conf:.3f}")
    if not results:
        print("  (no results)")

    print("\n=== small image test (original problem) ===")
    small = cv2.resize(plate, (150, 40), interpolation=cv2.INTER_AREA)
    print(f"small shape: {small.shape}")
    upscaled_small = ocr.upscale_roi(small)
    print(f"after upscale_roi: {upscaled_small.shape}")
    results_small = ocr.ocr_plate(small, full_image=plate)
    for text, conf in results_small:
        print(f"  text={text!r} conf={conf:.3f}")
    if not results_small:
        print("  (no results)")


if __name__ == "__main__":
    main()
