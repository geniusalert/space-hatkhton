import sqlite3

def init_db():
    try:
        conn = sqlite3.connect("cargo.db")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS items (
            itemId TEXT PRIMARY KEY, name TEXT, width REAL, depth REAL, height REAL,
            mass REAL, priority INTEGER, expiryDate TEXT, usageLimit INTEGER,
            preferredZone TEXT, containerId TEXT, startW REAL, startD REAL, startH REAL,
            endW REAL, endD REAL, endH REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS containers (
            containerId TEXT PRIMARY KEY, zone TEXT, width REAL, depth REAL, height REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
            timestamp TEXT, userId TEXT, actionType TEXT, itemId TEXT, details TEXT)''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()