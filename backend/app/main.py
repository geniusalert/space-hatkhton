from fastapi import FastAPI
from .database import init_db
import sqlite3

app = FastAPI()

def check_db_initialized():
    conn = sqlite3.connect("cargo.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
    exists = cursor.fetchone()
    conn.close()
    return exists is not None

if not check_db_initialized():
    init_db()