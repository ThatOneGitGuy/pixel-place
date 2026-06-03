import os
import random

DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    PH = '%s'
else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pixels.db")
    PH = '?'

def get_db():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    if USE_POSTGRES:
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                pixel_id TEXT UNIQUE
            )
        ''')
    else:
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
            color TEXT DEFAULT '#FFFFFF'
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
    c.execute(f"SELECT * FROM pixels WHERE pixel_id = {PH}", (pixel_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def claim_pixel(pixel_id, username, color):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(f"INSERT INTO pixels (pixel_id, owner, color) VALUES ({PH}, {PH}, {PH})", (pixel_id, username, color))
        c.execute(f"UPDATE users SET pixel_id = {PH} WHERE username = {PH}", (pixel_id, username))
        conn.commit()
        return True
    except Exception:
        conn.rollback() if USE_POSTGRES else None
        return False
    finally:
        conn.close()

def update_pixel_color(pixel_id, username, color):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"UPDATE pixels SET color = {PH} WHERE pixel_id = {PH} AND owner = {PH}", (color, pixel_id, username))
    conn.commit()
    conn.close()

def get_user(username):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE username = {PH}", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username, password_hash):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(f"INSERT INTO users (username, password_hash) VALUES ({PH}, {PH})", (username, password_hash))
        conn.commit()
        return True
    except Exception:
        conn.rollback() if USE_POSTGRES else None
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
    return random.sample(free, min(count, len(free)))

def generate_all_pixel_ids():
    ids = []
    for row in range(1, 301):
        for col in range(1, 301):
            ids.append(f"{row}-{col}")
    return ids

def is_valid_pixel_id(pixel_id):
    try:
        parts = pixel_id.split('-')
        if len(parts) != 2:
            return False
        row, col = int(parts[0]), int(parts[1])
        return 1 <= row <= 300 and 1 <= col <= 300
    except:
        return False