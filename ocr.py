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


def ocr_plate(image):
    """Run EasyOCR, return list of (text, confidence) tuples."""
    try:
        reader = get_reader()
        results = reader.readtext(image)
        return [(text, conf) for (_box, text, conf) in results]
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
