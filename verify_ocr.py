"""Independent verification: full app.py flow + edge cases."""
import numpy as np
import cv2
import ocr

print("=== TEST 1: full app.py flow on synthetic car scene ===")
# Build a 1200x800 scene: gray background with a white plate rectangle
scene = np.full((800, 1200, 3), 90, dtype=np.uint8)
# plate region: 360x120 at (400, 400)
px, py, pw, ph = 400, 400, 360, 120
cv2.rectangle(scene, (px, py), (px + pw, py + ph), (255, 255, 255), -1)
cv2.rectangle(scene, (px, py), (px + pw, py + ph), (0, 0, 0), 4)
text = "B 2301 PZX"
font = cv2.FONT_HERSHEY_SIMPLEX
scale, thick = 1.8, 4
(tw, th), _ = cv2.getTextSize(text, font, scale, thick)
cv2.putText(scene, text, (px + (pw - tw) // 2, py + (ph + th) // 2),
            font, scale, (0, 0, 0), thick, cv2.LINE_AA)

bbox = ocr.detect_plate_contour(scene)
print("detect_plate_contour ->", bbox)
roi = ocr.extract_plate_roi(scene, bbox) if bbox else scene
print("roi shape ->", None if roi is None else roi.shape)

results = ocr.ocr_plate(roi, full_image=scene)
print("ocr_plate results:")
for t, c in results:
    print(f"  {t!r}  conf={c:.3f}  norm={ocr.normalize_plate(t)!r}")
assert results, "FAIL: no OCR results"
best = max(results, key=lambda r: r[1])
assert ocr.normalize_plate(best[0]) == "B2301PZX", f"FAIL: got {best[0]!r}"
print("PASS: best =", best[0], f"({best[1]*100:.1f}%)")

print()
print("=== TEST 2: match_member with synthetic 'B 1234 ABC' ===")
# scene with a seeded member plate
scene2 = np.full((400, 600, 3), 90, dtype=np.uint8)
cv2.rectangle(scene2, (100, 140), (500, 260), (255, 255, 255), -1)
t2 = "B 1234 ABC"
(s2, tk2) = 2.0, 4
(tw2, th2), _ = cv2.getTextSize(t2, font, s2, tk2)
cv2.putText(scene2, t2, (100 + (400 - tw2) // 2, 140 + (120 + th2) // 2),
            font, s2, (0, 0, 0), tk2, cv2.LINE_AA)
bbox2 = ocr.detect_plate_contour(scene2)
roi2 = ocr.extract_plate_roi(scene2, bbox2) if bbox2 else scene2
res2 = ocr.ocr_plate(roi2, full_image=scene2)
best2 = max(res2, key=lambda r: r[1]) if res2 else ("", 0)
print("read:", best2[0], f"({best2[1]*100:.1f}%)")
member, match_type = ocr.match_member(best2[0])
print("match_member ->", member["nama"] if member else None, f"(type={match_type})")
assert member is not None and member["nama"] == "Budi Santoso", "FAIL: member match"
print("PASS: matched Budi Santoso")

print()
print("=== TEST 3: edge cases (no crash) ===")
print("ocr_plate(None) ->", ocr.ocr_plate(None))
empty = np.zeros((0, 0, 3), dtype=np.uint8)
print("ocr_plate(empty) ->", ocr.ocr_plate(empty))
tiny = np.full((5, 3, 3), 128, dtype=np.uint8)
print("ocr_plate(tiny 3x5) ->", ocr.ocr_plate(tiny))
print("upscale_roi(None) ->", ocr.upscale_roi(None))
print("PASS: no crashes on degenerate input")

print()
print("=== TEST 4: upscale_roi bounds ===")
small = np.zeros((40, 150, 3), dtype=np.uint8)
up = ocr.upscale_roi(small)
print("150px ->", up.shape[1], "(expect 400)")
big = np.zeros((3000, 4000, 3), dtype=np.uint8)
down = ocr.upscale_roi(big)
print("4000px ->", down.shape[1], "(expect 1000, memory cap)")
assert up.shape[1] == 400 and down.shape[1] == 1000
print("PASS: upscale + downscale caps work")

print()
print("ALL TESTS PASSED")
