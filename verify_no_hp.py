"""Verify no_hp removal: schema, seed, CRUD, and detection display."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db

print('=== 1. init_db (with legacy DB present) ===')
db.init_db()
conn = db.get_db()
cols = [r[1] for r in conn.execute('PRAGMA table_info(members)').fetchall()]
conn.close()
print('members columns:', cols)
assert 'no_hp' not in cols, 'no_hp still present!'
print('PASS: no_hp column gone')

print()
print('=== 2. seed_members ===')
db.seed_members()
members = db.get_all_members()
print(f'members: {len(members)}')
for m in members[:3]:
    print(' ', m)
    assert 'no_hp' not in m, f'no_hp leaked into dict: {m}'
print('PASS: no no_hp key in member dicts')

print()
print('=== 3. add_member (3-arg signature) ===')
new_id = db.add_member('Test User', 'B 9999 ZZZ', 'Mobil')
print('new id:', new_id)
assert new_id is not None
m = db.find_member_by_plate('B 9999 ZZZ')
print('found:', m)
assert m and 'no_hp' not in m
print('PASS')

print()
print('=== 4. update_member (3-arg signature) ===')
ok = db.update_member(new_id, 'Test User Edited', 'B 9999 ZZZ', 'Truk')
print('updated:', ok)
assert ok
m = db.find_member_by_plate('B 9999 ZZZ')
print('after update:', m['nama'], '/', m['jenis_kendaraan'])
assert m['nama'] == 'Test User Edited'
assert m['jenis_kendaraan'] == 'Truk'
print('PASS')

print()
print('=== 5. cleanup ===')
print('deleted:', db.delete_member(new_id))
print()
print('ALL TESTS PASSED')
