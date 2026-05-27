import sqlite3
import os

DB_PATH = "pixels.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            pixel_id TEXT UNIQUE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS pixels (
            pixel_id TEXT PRIMARY KEY,
            owner TEXT,
            color TEXT DEFAULT '#FFFFFF',
            FOREIGN KEY(owner) REFERENCES users(username)
        )
    ''')

    conn.commit()
    conn.close()

def get_all_pixels():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT pixel_id, owner, color FROM pixels")
    rows = c.fetchall()
    conn.close()
    return {row["pixel_id"]: {"owner": row["owner"], "color": row["color"]} for row in rows}

def get_pixel(pixel_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM pixels WHERE pixel_id = ?", (pixel_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def claim_pixel(pixel_id, username, color):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO pixels (pixel_id, owner, color) VALUES (?, ?, ?)", (pixel_id, username, color))
        c.execute("UPDATE users SET pixel_id = ? WHERE username = ?", (pixel_id, username))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_pixel_color(pixel_id, username, color):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE pixels SET color = ? WHERE pixel_id = ? AND owner = ?", (color, pixel_id, username))
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username, password_hash):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_free_pixels(count=1):
    """Get pixel IDs not yet claimed"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT pixel_id FROM pixels")
    taken = {row["pixel_id"] for row in c.fetchall()}
    conn.close()

    all_ids = generate_all_pixel_ids()
    free = [pid for pid in all_ids if pid not in taken]
    import random
    return random.sample(free, min(count, len(free)))

def generate_all_pixel_ids():
    """Generate all pixel IDs for a 200x200 grid"""
    ids = []
    cols = []
    for i in range(200):
        if i < 26:
            cols.append(chr(65 + i))
        elif i < 52:
            cols.append('A' + chr(65 + (i - 26)))
        elif i < 78:
            cols.append('B' + chr(65 + (i - 52)))
        else:
            cols.append('C' + chr(65 + (i - 78)))
    for col in cols:
        for row in range(1, 201):
            ids.append(f"{col}{row}")
    return ids