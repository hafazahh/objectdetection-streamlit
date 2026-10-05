"""Verify explicit-column queries hide legacy no_hp even on an old schema."""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Build a legacy DB that still has no_hp, in a temp path, then point db at it.
LEGACY = os.path.join(HERE, 'legacy_test.db')
if os.path.exists(LEGACY):
    os.remove(LEGACY)

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
    "VALUES ('Legacy User', 'B 0001 LEG', 'Mobil', '081200000000')"
)
conn.commit()
conn.close()

import db
db.DB_PATH = LEGACY  # point the module at the legacy DB

print('=== legacy DB columns ===')
c = db.get_db()
cols = [r[1] for r in c.execute('PRAGMA table_info(members)').fetchall()]
c.close()
print(cols)
assert 'no_hp' in cols, 'setup failed: legacy DB should have no_hp'
print('PASS: legacy DB does have no_hp (the risky case)')

print()
print('=== get_all_members() on legacy schema ===')
members = db.get_all_members()
print(members)
for m in members:
    assert 'no_hp' not in m, f'LEAK: {m}'
print('PASS: no_hp NOT leaked by get_all_members()')

print()
print('=== find_member_by_plate() on legacy schema ===')
m = db.find_member_by_plate('B 0001 LEG')
print(m)
assert m and 'no_hp' not in m, f'LEAK: {m}'
print('PASS: no_hp NOT leaked by find_member_by_plate()')

os.remove(LEGACY)
print()
print('ALL TESTS PASSED')
