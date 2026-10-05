import cv2
import numpy as np
import streamlit as st


@st.cache_resource
def get_reader():
    """Cache EasyOCR reader so it is not reloaded on every rerun."""
    import easyocr
    return easyocr.Reader(['en'], gpu=False)


def preprocess_image(image):
    """Resize to max 800px width, grayscale, Gaussian blur, adaptive threshold."""
    h, w = image.shape[:2]
    if w > 800:
        scale = 800 / w
        image = cv2.resize(image, (800, int(h * scale)))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return thresh


def detect_plate_contour(image):
    """Find contours, filter by aspect ratio (2:1 to 5:1), return best (x, y, w, h)."""
    processed = preprocess_image(image)
    contours, _ = cv2.findContours(processed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

    best = None
    best_area = 0
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h == 0:
            continue
        aspect = w / h
        if 2.0 <= aspect <= 5.0:
            area = cv2.contourArea(contour)
            if area > best_area:
                best_area = area
                best = (x, y, w, h)
    return best


def extract_plate_roi(image, bbox):
    """Extract region of interest from image given (x, y, w, h)."""
    if bbox is None:
        return None
    x, y, w, h = bbox
    return image[y:y + h, x:x + w]


def upscale_roi(image, min_width=400, max_width=1000):
    """Bring ROI width into [min_width, max_width] using INTER_CUBIC/INTER_AREA."""
    if image is None or image.size == 0:
        return None
    h, w = image.shape[:2]
    if w == 0 or h == 0:
        return None
    if w < min_width:
        scale = min_width / w
        image = cv2.resize(image, (min_width, int(h * scale)), interpolation=cv2.INTER_CUBIC)
    elif w > max_width:
        scale = max_width / w
        image = cv2.resize(image, (max_width, int(h * scale)), interpolation=cv2.INTER_AREA)
    return image


def generate_variants(image):
    """Generate preprocessing variants of a BGR image for OCR attempts."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    clahe_img = cv2.cvtColor(clahe.apply(gray), cv2.COLOR_GRAY2BGR)

    _, otsu_gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    otsu_img = cv2.cvtColor(otsu_gray, cv2.COLOR_GRAY2BGR)

    _, otsu_inv_gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    otsu_inv_img = cv2.cvtColor(otsu_inv_gray, cv2.COLOR_GRAY2BGR)

    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    sharpened = cv2.addWeighted(image, 1.5, blurred, -0.5, 0)

    return {
        "original": image,
        "clahe": clahe_img,
        "otsu": otsu_img,
        "otsu_inv": otsu_inv_img,
        "sharpened": sharpened,
    }


def ocr_plate(image, full_image=None):
    """Run EasyOCR with multi-variant preprocessing, return list of (text, confidence)."""
    if image is None:
        return []
    try:
        reader = get_reader()
        allowlist = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
        results = []

        upscaled = upscale_roi(image)
        if upscaled is None or upscaled.size == 0:
            return []

        for variant in generate_variants(upscaled).values():
            for (_box, text, conf) in reader.readtext(variant, allowlist=allowlist):
                results.append((text, conf))

        if not results and full_image is not None and full_image is not image:
            full_upscaled = upscale_roi(full_image)
            if full_upscaled is not None and full_upscaled.size > 0:
                for variant in generate_variants(full_upscaled).values():
                    for (_box, text, conf) in reader.readtext(variant, allowlist=allowlist):
                        results.append((text, conf))

        best = {}
        for text, conf in results:
            key = normalize_plate(text)
            if not key:
                continue
            if key not in best or conf > best[key][1]:
                best[key] = (text, conf)

        deduped = sorted(best.values(), key=lambda r: r[1], reverse=True)
        return deduped
    except Exception as e:
        st.error(f'Gagal menjalankan OCR: {e}')
        return []


def normalize_plate(text):
    """Uppercase, keep only A-Z and 0-9, remove spaces."""
    text = text.upper()
    return ''.join(c for c in text if c.isalnum() and ('A' <= c <= 'Z' or c.isdigit()))


def match_member(plat_nomor):
    """Normalize input, find member by exact match on normalized plate."""
    import db
    normalized = normalize_plate(plat_nomor)
    if not normalized:
        return None
    for member in db.get_all_members():
        if normalize_plate(member['plat_nomor']) == normalized:
            return member
    return None
