"""Test CURRENT init_db() against a legacy DB that still has no_hp (the cloud case)."""
import os
import sqlite3
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

LEGACY = os.path.join(HERE, 'legacy_migration_test.db')
for suffix in ['', '-wal', '-shm']:
    p = LEGACY + suffix
    if os.path.exists(p):
        os.remove(p)

# Build a legacy DB exactly like the pre-fffe466 schema
conn = sqlite3.connect(LEGACY)
conn.execute('''
    CREATE TABLE members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        plat_nomor TEXT NOT NULL UNIQUE,
        jenis_kendaraan TEXT DEFAULT 'Mobil',
        no_hp TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.execute(
    "INSERT INTO members (nama, plat_nomor, jenis_kendaraan, no_hp) "
    "VALUES ('Legacy', 'B 0001 LEG', 'Mobil', '0812')"
)
conn.execute('''
    CREATE TABLE detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plat_nomor TEXT NOT NULL,
        member_id INTEGER,
        match_status TEXT NOT NULL,
        image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()

import db
db.DB_PATH = LEGACY

print('=== legacy columns BEFORE init_db ===')
c = sqlite3.connect(LEGACY)
print([r[1] for r in c.execute('PRAGMA table_info(members)')])
c.close()

print()
print('=== calling db.init_db() on legacy DB (this is what the cloud does) ===')
try:
    db.init_db()
    print('init_db: OK')
except Exception:
    print('!!! init_db RAISED — this would crash the Streamlit script !!!')
    traceback.print_exc()
    sys.exit(1)

print()
print('=== columns AFTER ===')
c = sqlite3.connect(LEGACY)
print([r[1] for r in c.execute('PRAGMA table_info(members)')])
c.close()

print()
print('=== seed_members + queries ===')
try:
    db.seed_members()
    print('rows:', len(db.get_all_members()))
    print('stats:', db.get_detection_stats())
    print('OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)

for suffix in ['', '-wal', '-shm']:
    p = LEGACY + suffix
    if os.path.exists(p):
        os.remove(p)

print()
print('LEGACY MIGRATION TEST PASSED')
