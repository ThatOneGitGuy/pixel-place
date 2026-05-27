import sqlite3
import os

DB_PATH = "/app/data/pixels.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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
    conn.clo