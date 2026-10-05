"""Reproduce the Streamlit Cloud startup path locally and time each step."""
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

t0 = time.time()


def mark(label):
    print(f"[{time.time() - t0:7.2f}s] {label}", flush=True)


mark("start")

try:
    mark("import cv2 ...")
    import cv2
    mark(f"cv2 {cv2.__version__}")

    mark("import db ...")
    import db
    mark("db imported")

    mark("db.init_db() ...")
    db.init_db()
    mark("init_db OK")

    mark("db.seed_members() ...")
    db.seed_members()
    mark("seed_members OK")

    cols = [r[1] for r in db.get_db().execute('PRAGMA table_info(members)').fetchall()]
    mark(f"members columns = {cols}")

    n = len(db.get_all_members())
    mark(f"get_all_members -> {n} rows")

    stats = db.get_detection_stats()
    mark(f"get_detection_stats -> {stats}")

    mark("import ocr (pulls streamlit) ...")
    import ocr
    mark("ocr imported")

    mark("import easyocr + build Reader (the slow part) ...")
    reader = ocr.get_reader.__wrapped__()
    mark("EasyOCR Reader ready")

    mark("ALL STARTUP STEPS OK")
except Exception:
    mark("!!! STARTUP FAILED !!!")
    traceback.print_exc()
    sys.exit(1)
