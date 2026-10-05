import re
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


# Indonesian plate pattern: 1-2 letters + 1-4 digits + 1-3 letters
PLATE_PATTERN = re.compile(r'^[A-Z]{1,2}[0-9]{1,4}[A-Z]{1,3}$')

# Confusion pairs: digit misread as letter (for letter positions)
DIGIT_TO_LETTER = {'0': 'O', '1': 'I', '8': 'B', '5': 'S', '2': 'Z', '6': 'G'}
# Confusion pairs: letter misread as digit (for digit positions)
LETTER_TO_DIGIT = {'O': '0', 'I': '1', 'B': '8', 'S': '5', 'Z': '2', 'G': '6', 'D': '0', 'Q': '0'}


def correct_plate_format(text):
    """
    Correct OCR output to match Indonesian plate format.
    Returns (corrected_text, was_corrected).
    Conservative: if cannot confidently repair, return original unchanged.
    """
    normalized = normalize_plate(text)
    if not normalized:
        return text, False

    # Already valid
    if PLATE_PATTERN.match(normalized):
        return normalized, False

    # Try to repair
    corrected = _try_repair(normalized)
    if corrected and PLATE_PATTERN.match(corrected):
        return corrected, True

    return normalized, False


def _try_repair(text):
    """
    Attempt to repair a plate string into valid Indonesian format.
    Try all possible (lead, digit, trail) splits and apply confusion corrections.
    Return the best candidate or None.
    """
    n = len(text)
    if n < 3:  # minimum: 1 letter + 1 digit + 1 letter
        return None

    best_candidate = None
    best_score = -float('inf')

    # Try all possible splits: leading letters (1-2), middle digits (1-4), trailing letters (1-3)
    for lead_len in range(1, min(3, n)):  # 1-2 leading letters
        for digit_len in range(1, min(5, n - lead_len)):  # 1-4 digits
            trail_len = n - lead_len - digit_len
            if trail_len < 1 or trail_len > 3:
                continue

            lead = text[:lead_len]
            digits = text[lead_len:lead_len + digit_len]
            trail = text[lead_len + digit_len:]

            # Apply corrections
            corrected_lead = ''.join(DIGIT_TO_LETTER.get(c, c) for c in lead)
            corrected_digits = ''.join(LETTER_TO_DIGIT.get(c, c) for c in digits)
            corrected_trail = ''.join(DIGIT_TO_LETTER.get(c, c) for c in trail)

            candidate = corrected_lead + corrected_digits + corrected_trail

            if PLATE_PATTERN.match(candidate):
                # Score: prefer candidates that require fewer corrections
                corrections = sum(1 for a, b in zip(text, candidate) if a != b)
                score = -corrections  # fewer corrections = higher score
                if score > best_score:
                    best_score = score
                    best_candidate = candidate

    return best_candidate


def match_member(plat_nomor):
    """
    Normalize input, find member by exact match first, then fuzzy fallback.
    Returns (member_dict, match_type) where match_type is 'exact', 'fuzzy', or None.
    """
    import db
    from difflib import SequenceMatcher

    normalized = normalize_plate(plat_nomor)
    if not normalized:
        return None, None

    members = db.get_all_members()

    # 1. Exact match (fast path)
    for member in members:
        if normalize_plate(member['plat_nomor']) == normalized:
            return member, 'exact'

    # 2. Fuzzy fallback
    best_match = None
    best_ratio = 0.0
    second_best_ratio = 0.0

    for member in members:
        member_plate = normalize_plate(member['plat_nomor'])
        if not member_plate:
            continue

        # Length difference guard: at most 1
        if abs(len(normalized) - len(member_plate)) > 1:
            continue

        ratio = SequenceMatcher(None, normalized, member_plate).ratio()

        if ratio > best_ratio:
            second_best_ratio = best_ratio
            best_ratio = ratio
            best_match = member
        elif ratio > second_best_ratio:
            second_best_ratio = ratio

    # Accept only if ratio >= 0.85 and strictly better than second best
    if best_match and best_ratio >= 0.85 and best_ratio > second_best_ratio:
        return best_match, 'fuzzy'

    return None, None
