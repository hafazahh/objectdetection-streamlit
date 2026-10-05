import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'anpr.db')


def get_db():
    """Return sqlite3 connection with row_factory = sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create members and detections tables."""
    conn = get_db()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                plat_nomor TEXT NOT NULL UNIQUE,
                jenis_kendaraan TEXT DEFAULT 'Mobil',
                no_hp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plat_nomor TEXT NOT NULL,
                member_id INTEGER,
                match_status TEXT NOT NULL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(id)
            )
        ''')
        conn.commit()
    finally:
        conn.close()


def seed_members():
    """Insert 5 sample members if the members table is empty."""
    conn = get_db()
    try:
        count = conn.execute('SELECT COUNT(*) FROM members').fetchone()[0]
        if count == 0:
            sample = [
                ('Budi Santoso', 'B 1234 ABC', 'Mobil', '081234567890'),
                ('Siti Rahayu', 'D 5678 XYZ', 'Motor', '081298765432'),
                ('Andi Wijaya', 'F 9012 DEF', 'Mobil', '082111223344'),
                ('Dewi Lestari', 'L 3456 GHI', 'Motor', '085755667788'),
                ('Joko Prasetyo', 'Z 7890 JKL', 'Truk', '087899112233'),
            ]
            conn.executemany(
                'INSERT INTO members (nama, plat_nomor, jenis_kendaraan, no_hp) VALUES (?, ?, ?, ?)',
                sample,
            )
            conn.commit()
    finally:
        conn.close()


def get_all_members():
    """Return list of all members as dicts."""
    conn = get_db()
    try:
        rows = conn.execute('SELECT * FROM members ORDER BY id').fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def add_member(nama, plat_nomor, jenis_kendaraan, no_hp):
    """Insert member, return new id or None on error."""
    conn = get_db()
    try:
        cur = conn.execute(
            'INSERT INTO members (nama, plat_nomor, jenis_kendaraan, no_hp) VALUES (?, ?, ?, ?)',
            (nama, plat_nomor, jenis_kendaraan, no_hp),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def update_member(id, nama, plat_nomor, jenis_kendaraan, no_hp):
    """Update member, return True/False."""
    conn = get_db()
    try:
        cur = conn.execute(
            'UPDATE members SET nama=?, plat_nomor=?, jenis_kendaraan=?, no_hp=? WHERE id=?',
            (nama, plat_nomor, jenis_kendaraan, no_hp, id),
        )
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def delete_member(id):
    """Delete member, return True/False."""
    conn = get_db()
    try:
        cur = conn.execute('DELETE FROM members WHERE id=?', (id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def find_member_by_plate(plat_nomor):
    """Return member dict or None."""
    conn = get_db()
    try:
        row = conn.execute(
            'SELECT * FROM members WHERE plat_nomor=?', (plat_nomor,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_detection(plat_nomor, member_id, match_status, image_path):
    """Insert detection, return new id."""
    conn = get_db()
    try:
        cur = conn.execute(
            'INSERT INTO detections (plat_nomor, member_id, match_status, image_path) VALUES (?, ?, ?, ?)',
            (plat_nomor, member_id, match_status, image_path),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_all_detections():
    """Return list of all detections as dicts."""
    conn = get_db()
    try:
        rows = conn.execute('SELECT * FROM detections ORDER BY id DESC').fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_detection(id):
    """Delete detection, return True/False."""
    conn = get_db()
    try:
        cur = conn.execute('DELETE FROM detections WHERE id=?', (id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def get_detection_stats():
    """Return dict with total_members, total_detections, matched_count, unmatched_count."""
    conn = get_db()
    try:
        total_members = conn.execute('SELECT COUNT(*) FROM members').fetchone()[0]
        total_detections = conn.execute('SELECT COUNT(*) FROM detections').fetchone()[0]
        matched_count = conn.execute(
            "SELECT COUNT(*) FROM detections WHERE match_status='matched'"
        ).fetchone()[0]
        unmatched_count = conn.execute(
            "SELECT COUNT(*) FROM detections WHERE match_status='unmatched'"
        ).fetchone()[0]
        return {
            'total_members': total_members,
            'total_detections': total_detections,
            'matched_count': matched_count,
            'unmatched_count': unmatched_count,
        }
    finally:
        conn.close()
