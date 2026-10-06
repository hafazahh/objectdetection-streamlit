"""INDEPENDENT verification — cases NOT in the agent's own test file.
Focus: edge cases + false-positive hunting on fuzzy match.
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ocr
import db

print('=' * 64)
print('A. FORMAT CORRECTION — edge cases (not in agent test)')
print('=' * 64)
cases = [
    ('AB1234CD', '2 lead + 2 trail = valid', False),
    ('A1234B',   '1 lead + 1 trail = valid', False),
    ('B12345AB', 'ACCEPTED behaviour: repairs to B1234SAB (see note)', True),
    ('B1234ABCD', '4 trailing letters = invalid, keep', False),
    ('ABC1234AB', '3 leading letters = invalid, keep', False),
    ('',          'empty', False),
    ('O1234O',   'O is not in digit->letter map, stays valid', False),
    ('01234O1',  '0->O lead, 1->I trail', True),
    ('D1234ABC', 'D at lead: D is a real letter, valid', False),
    ('8',        'single char', False),
    ('B1C',      '1 lead 1 digit 1 trail = valid', False),
]
fails = 0
for text, note, expect_corrected in cases:
    out, was = ocr.correct_plate_format(text)
    ok = (was == expect_corrected)
    if not ok:
        fails += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {text!r:14} -> {out!r:14} corrected={was}  ({note})")

print()
print('=' * 64)
print('B. FUZZY MATCH — false positive hunt')
print('=' * 64)

# Use a scratch DB so we can inject lookalike members
SCRATCH = os.path.join(HERE, 'indep_scratch.db')
for s in ['', '-wal', '-shm']:
    p = SCRATCH + s
    if os.path.exists(p):
        os.remove(p)

conn = sqlite3.connect(SCRATCH)
conn.execute('''CREATE TABLE members (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT NOT NULL,
    plat_nomor TEXT NOT NULL UNIQUE, jenis_kendaraan TEXT DEFAULT 'Mobil',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.execute('''CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT, plat_nomor TEXT NOT NULL,
    member_id INTEGER, match_status TEXT NOT NULL, image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
# Deliberately adversarial: two members that differ by ONE char
conn.executemany(
    'INSERT INTO members (nama, plat_nomor, jenis_kendaraan) VALUES (?,?,?)',
    [('Budi Santoso', 'B 1234 ABC', 'Mobil'),
     ('Budi Kembar', 'B 1234 ABD', 'Mobil'),   # 1 char from Budi Santoso
     ('Siti Rahayu', 'D 5678 XYZ', 'Motor')]
)
conn.commit()
conn.close()

db.DB_PATH = SCRATCH

print('  Members seeded (adversarial):')
for m in db.get_all_members():
    print(f"    {m['id']}: {m['nama']} — {m['plat_nomor']}")
print()

fuzzy_cases = [
    ('B1234ABC', 'exact match, Budi Santoso', 'exact', 'Budi Santoso'),
    ('B1234ABD', 'exact match, Budi Kembar', 'exact', 'Budi Kembar'),
    # 'B1234ABE' is 1 char from BOTH B1234ABC and B1234ABD -> ambiguity -> must be None
    ('B1234ABE', 'ambiguous between two members -> MUST be None', None, None),
    ('D5678XYA', '1 char from Siti -> fuzzy', 'fuzzy', 'Siti Rahayu'),
    ('X9999XXX', 'nothing close -> None', None, None),
    ('B9999ABC', '3 chars off -> None (below 0.85)', None, None),
]
for text, note, exp_type, exp_name in fuzzy_cases:
    # match_member now also returns (similarity, runner_up) percentages
    member, mtype, sim, runner = ocr.match_member(text)
    name = member['nama'] if member else None
    ok = (mtype == exp_type and name == exp_name)
    if not ok:
        fails += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {text!r:11} -> type={str(mtype):7} "
          f"name={str(name):14} sim={sim:5.1f}% runner={runner:5.1f}%  ({note})")
    if not ok:
        print(f"          expected type={exp_type!r} name={exp_name!r}")

for s in ['', '-wal', '-shm']:
    p = SCRATCH + s
    if os.path.exists(p):
        os.remove(p)

print()
print('=' * 64)
print(f"RESULT: {'ALL INDEPENDENT CHECKS PASSED' if fails == 0 else f'{fails} CHECK(S) FAILED'}")
print('=' * 64)
sys.exit(0 if fails == 0 else 1)
