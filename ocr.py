"""ANPR OCR module — YOLO plate detection + Tesseract recognition.

Pipeline (Phase 11):
  1. YOLO detects the plate bounding box (learned, replaces the old contour guess)
  2. Crop the ROI from that box
  3. Tesseract reads it across multiple preprocessing variants and PSM modes
  4. Candidates are VOTED on: agreement across variants beats a single lucky read
  5. The winner is corrected to Indonesian plate format
  6. The result is compared to the member database and scored as a percentage

Why Tesseract instead of EasyOCR: measured peak RAM drops from 1253 MB to
857 MB, which shortens the Streamlit cold start (the cause of the "Server Error"
seen for 45-120s on wake).
"""
import os
import re
from collections import defaultdict

import cv2
import numpy as np
import pytesseract
import streamlit as st

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'models', 'plate_yolov8.pt')

# Tesseract reads dark-on-light; Indonesian plates come in both polarities, so
# both the normal and inverted image are tried (see generate_variants).
ALLOWLIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
PSM_MODES = (7, 8, 6)   # single line / single word / uniform block


@st.cache_resource
def get_model():
    """Cache the YOLO model so it is not reloaded on every Streamlit rerun."""
    from ultralytics import YOLO
    if not os.path.exists(MODEL_PATH):
        return None
    return YOLO(MODEL_PATH)


# ---------------------------------------------------------------------------
# Step 1 — plate detection
# ---------------------------------------------------------------------------
def detect_plate_yolo(image, conf=0.25, imgsz=640):
    """Detect the plate with YOLO.

    Returns (bbox, confidence) where bbox is (x, y, w, h), or (None, 0.0).
    Picks the highest-confidence box when several are returned.
    """
    model = get_model()
    if model is None or image is None or image.size == 0:
        return None, 0.0
    try:
        results = model.predict(image, conf=conf, imgsz=imgsz, verbose=False)
        if not results or results[0].boxes is None or len(results[0].boxes) == 0:
            return None, 0.0
        boxes = results[0].boxes
        confs = boxes.conf.cpu().numpy()
        best = int(np.argmax(confs))
        x1, y1, x2, y2 = boxes.xyxy.cpu().numpy()[best]
        x, y = int(max(0, x1)), int(max(0, y1))
        w, h = int(x2 - x1), int(y2 - y1)
        if w <= 0 or h <= 0:
            return None, 0.0
        return (x, y, w, h), float(confs[best])
    except Exception as e:
        st.error(f'Gagal menjalankan deteksi YOLO: {e}')
        return None, 0.0


def extract_plate_roi(image, bbox, pad=4):
    """Crop the ROI from (x, y, w, h) with a small padding so edge characters
    are not clipped by an over-tight box."""
    if bbox is None or image is None:
        return None
    x, y, w, h = bbox
    ih, iw = image.shape[:2]
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(iw, x + w + pad), min(ih, y + h + pad)
    roi = image[y0:y1, x0:x1]
    return roi if roi.size else None


def detect_plate_contour(image):
    """Legacy OpenCV contour detector, kept as a fallback when YOLO finds nothing.

    Guesses the plate by aspect ratio, which is why it is no longer the primary
    method — on real photos it often locks onto a bumper or window instead.
    """
    if image is None or image.size == 0:
        return None
    h, w = image.shape[:2]
    if w > 800:
        scale = 800 / w
        image = cv2.resize(image, (800, int(h * scale)))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

    best, best_area = None, 0
    for contour in contours:
        x, y, ww, hh = cv2.boundingRect(contour)
        if hh == 0:
            continue
        if 2.0 <= ww / hh <= 5.0:
            area = cv2.contourArea(contour)
            if area > best_area:
                best_area, best = area, (x, y, ww, hh)
    return best


def upscale_roi(image, min_width=500, max_width=1400):
    """Bring ROI width into range. Tesseract wants reasonably large glyphs."""
    if image is None or image.size == 0:
        return None
    h, w = image.shape[:2]
    if w == 0 or h == 0:
        return None
    if w < min_width:
        scale = min_width / w
        return cv2.resize(image, (min_width, int(h * scale)),
                          interpolation=cv2.INTER_CUBIC)
    if w > max_width:
        scale = max_width / w
        return cv2.resize(image, (max_width, int(h * scale)),
                          interpolation=cv2.INTER_AREA)
    return image


# ---------------------------------------------------------------------------
# Step 2 — preprocessing variants
# ---------------------------------------------------------------------------
def generate_variants(image):
    """BGR image -> dict of grayscale variants.

    Includes INVERTED versions because Indonesian plates are frequently white
    characters on a black background, which Tesseract cannot read directly.
    """
    up = upscale_roi(image)
    if up is None:
        return {}
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    inv = cv2.bitwise_not(gray)

    variants = {'gray': gray, 'inv': inv}
    for tag, base in (('g', gray), ('i', inv)):
        _, otsu = cv2.threshold(base, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants[f'{tag}_otsu'] = otsu
        variants[f'{tag}_clahe'] = cv2.createCLAHE(clipLimit=2.0,
                                                   tileGridSize=(8, 8)).apply(base)
    return variants


# ---------------------------------------------------------------------------
# Step 3 — recognition (voting)
# ---------------------------------------------------------------------------
def _read_one(img, psm):
    """Run Tesseract once, return (normalized_text, mean_confidence)."""
    cfg = f'--psm {psm} -c tessedit_char_whitelist={ALLOWLIST}'
    text = pytesseract.image_to_string(img, config=cfg).strip()
    if not text:
        return '', 0.0
    norm = ''.join(ch for ch in text.upper() if ch in ALLOWLIST)
    if not norm:
        return '', 0.0
    try:
        data = pytesseract.image_to_data(img, config=cfg,
                                         output_type=pytesseract.Output.DICT)
        confs = []
        for c in data['conf']:
            try:
                v = int(c)
                if v >= 0:
                    confs.append(v)
            except (TypeError, ValueError):
                pass
        conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
    except Exception:
        conf = 0.0
    return norm, conf


def ocr_plate(image, full_image=None):
    """Read a plate ROI with Tesseract and vote across variants.

    Returns a list of (text, score) sorted best-first, where score blends how
    many variants agreed, their mean confidence, and plate-format validity.
    """
    if image is None or image.size == 0:
        return []
    try:
        variants = generate_variants(image)
        if not variants:
            return []

        candidates = []
        for vimg in variants.values():
            for psm in PSM_MODES:
                text, conf = _read_one(vimg, psm)
                if text:
                    candidates.append((text, conf))

        # Fallback: if the ROI yielded nothing, try the whole image
        if not candidates and full_image is not None and full_image is not image:
            for vimg in generate_variants(full_image).values():
                for psm in PSM_MODES:
                    text, conf = _read_one(vimg, psm)
                    if text:
                        candidates.append((text, conf))

        if not candidates:
            return []

        return _vote(candidates)
    except Exception as e:
        st.error(f'Gagal menjalankan OCR: {e}')
        return []


def _vote(candidates):
    """Group identical reads and rank them.

    Voting beats trusting the single highest-confidence read: one variant can
    return a confident but wrong string, whereas the correct plate usually
    reappears across several variants.
    """
    groups = defaultdict(list)
    for text, conf in candidates:
        groups[text].append(conf)

    scored = []
    for text, confs in groups.items():
        votes = len(confs)
        mean_conf = sum(confs) / votes
        corrected, _ = correct_plate_format(text)
        valid = bool(PLATE_PATTERN.match(corrected))
        score = votes + mean_conf * 2.0 + (1.5 if valid else 0.0)
        scored.append((text, score))

    scored.sort(key=lambda r: r[1], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Step 4 — normalisation and format correction
# ---------------------------------------------------------------------------
def normalize_plate(text):
    """Uppercase, keep only A-Z and 0-9, remove spaces."""
    text = text.upper()
    return ''.join(c for c in text if c.isalnum() and ('A' <= c <= 'Z' or c.isdigit()))


# Indonesian plate pattern: 1-2 letters + 1-4 digits + 1-3 letters
PLATE_PATTERN = re.compile(r'^[A-Z]{1,2}[0-9]{1,4}[A-Z]{1,3}$')

# Confusion pairs: digit misread as letter (for letter positions)
DIGIT_TO_LETTER = {'0': 'O', '1': 'I', '8': 'B', '5': 'S', '2': 'Z', '6': 'G'}
# Confusion pairs: letter misread as digit (for digit positions)
LETTER_TO_DIGIT = {'O': '0', 'I': '1', 'B': '8', 'S': '5', 'Z': '2', 'G': '6',
                   'D': '0', 'Q': '0'}


def correct_plate_format(text):
    """Correct OCR output to match Indonesian plate format.

    Returns (corrected_text, was_corrected). Conservative: if it cannot
    confidently repair the string, the original is returned unchanged.
    """
    normalized = normalize_plate(text)
    if not normalized:
        return text, False

    if PLATE_PATTERN.match(normalized):
        return normalized, False

    corrected = _try_repair(normalized)
    if corrected and PLATE_PATTERN.match(corrected):
        return corrected, True

    return normalized, False


def _try_repair(text):
    """Try all (lead, digit, trail) splits with confusion corrections applied.

    Returns the candidate needing the fewest corrections, or None.
    """
    n = len(text)
    if n < 3:   # minimum: 1 letter + 1 digit + 1 letter
        return None

    best_candidate, best_score = None, -float('inf')

    for lead_len in range(1, min(3, n)):
        for digit_len in range(1, min(5, n - lead_len)):
            trail_len = n - lead_len - digit_len
            if trail_len < 1 or trail_len > 3:
                continue

            lead = text[:lead_len]
            digits = text[lead_len:lead_len + digit_len]
            trail = text[lead_len + digit_len:]

            candidate = (
                ''.join(DIGIT_TO_LETTER.get(c, c) for c in lead)
                + ''.join(LETTER_TO_DIGIT.get(c, c) for c in digits)
                + ''.join(DIGIT_TO_LETTER.get(c, c) for c in trail)
            )

            if PLATE_PATTERN.match(candidate):
                corrections = sum(1 for a, b in zip(text, candidate) if a != b)
                score = -corrections
                if score > best_score:
                    best_score, best_candidate = score, candidate

    return best_candidate


# ---------------------------------------------------------------------------
# Step 5 — member matching with a similarity percentage
# ---------------------------------------------------------------------------
def plate_similarity(a, b):
    """Similarity of two plates as a 0-100 percentage.

    Blends character-sequence ratio with position-weighted agreement and a
    bonus for a matching leading letter, which encodes the registration region.
    """
    from difflib import SequenceMatcher

    na, nb = normalize_plate(a), normalize_plate(b)
    if not na or not nb:
        return 0.0

    ratio = SequenceMatcher(None, na, nb).ratio()
    same = sum(1 for x, y in zip(na, nb) if x == y)
    positional = same / max(len(na), len(nb))
    lead_match = 1.0 if na[:1] == nb[:1] else 0.0

    score = (ratio * 0.55) + (positional * 0.30) + (lead_match * 0.15)
    return round(score * 100, 1)


def match_member(plat_nomor, threshold=70.0):
    """Find the member whose plate is most similar.

    Returns (member, match_type, similarity_percent, runner_up_percent).
    match_type is 'exact', 'fuzzy', or None. The runner-up percentage lets the
    caller show how far the winner stood out from the next best candidate.
    """
    import db

    normalized = normalize_plate(plat_nomor)
    if not normalized:
        return None, None, 0.0, 0.0

    members = db.get_all_members()
    if not members:
        return None, None, 0.0, 0.0

    # 1. Exact match
    for member in members:
        if normalize_plate(member['plat_nomor']) == normalized:
            return member, 'exact', 100.0, 0.0

    # 2. Score every member
    scored = [(plate_similarity(normalized, m['plat_nomor']), m) for m in members]
    scored.sort(key=lambda t: t[0], reverse=True)

    best_sim, best_member = scored[0]
    runner_up = scored[1][0] if len(scored) > 1 else 0.0

    # Accept only above threshold and only if the winner is clearly ahead —
    # otherwise two near-identical plates make the answer a coin flip.
    if best_sim >= threshold and (best_sim - runner_up) >= 5.0:
        return best_member, 'fuzzy', best_sim, runner_up

    return None, None, best_sim, runner_up
