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
    """Generate all pixel IDs for a 300x300 grid using row-col format: 1-1 to 300-300"""
    ids = []
    for row in range(1, 301):
        for col in range(1, 301):
            ids.append(f"{row}-{col}")
    return ids

def is_valid_pixel_id(pixel_id):
    """Check if a pixel ID is valid for a 300x300 grid"""
    try:
        parts = pixel_id.split('-')
        if len(parts) != 2:
            return False
        row, col = int(parts[0]), int(parts[1])
        return 1 <= row <= 300 and 1 <= col <= 300
    except:
        return False