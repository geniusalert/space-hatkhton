import sqlite3
from typing import Optional, List, Dict, Any
from fastapi import Depends
from .schemas import Item, Container, Log

# Connection pool using FastAPI dependency injection
def get_db():
    conn = sqlite3.connect("cargo.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# --- Item CRUD Operations ---
def create_item(item: Item, db: sqlite3.Connection = Depends(get_db)) -> bool:
    """Create a new item in the database."""
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO items (itemId, name, width, depth, height, mass, priority, expiryDate, usageLimit, preferredZone, 
                              containerId, startW, startD, startH, endW, endD, endH)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item.itemId, item.name, item.width, item.depth, item.height, item.mass, item.priority, item.expiryDate,
              item.usageLimit, item.preferredZone, item.containerId if item.containerId else None,
              item.startW if item.startW else None, item.startD if item.startD else None, item.startH if item.startH else None,
              item.endW if item.endW else None, item.endD if item.endD else None, item.endH if item.endH else None))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Duplicate itemId
    finally:
        cursor.close()

def get_item(item_id: str, db: sqlite3.Connection = Depends(get_db)) -> Optional[Dict[str, Any]]:
    """Retrieve an item by its ID."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM items WHERE itemId = ?", (item_id,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return dict(row)
    return None

def update_item(item_id: str, updates: Dict[str, Any], db: sqlite3.Connection = Depends(get_db)) -> bool:
    """Update an existing item's fields."""
    cursor = db.cursor()
    set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
    values = list(updates.values()) + [item_id]
    cursor.execute(f"UPDATE items SET {set_clause} WHERE itemId = ?", values)
    affected = cursor.rowcount > 0
    db.commit()
    cursor.close()
    return affected

def delete_item(item_id: str, db: sqlite3.Connection = Depends(get_db)) -> bool:
    """Delete an item by its ID."""
    cursor = db.cursor()
    cursor.execute("DELETE FROM items WHERE itemId = ?", (item_id,))
    affected = cursor.rowcount > 0
    db.commit()
    cursor.close()
    return affected

# --- Container CRUD Operations ---
def create_container(container: Container, db: sqlite3.Connection = Depends(get_db)) -> bool:
    """Create a new container in the database."""
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO containers (containerId, zone, width, depth, height)
            VALUES (?, ?, ?, ?, ?)
        """, (container.containerId, container.zone, container.width, container.depth, container.height))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Duplicate containerId
    finally:
        cursor.close()

def get_container(container_id: str, db: sqlite3.Connection = Depends(get_db)) -> Optional[Dict[str, Any]]:
    """Retrieve a container by its ID."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM containers WHERE containerId = ?", (container_id,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return dict(row)
    return None

def get_all_containers(db: sqlite3.Connection = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve all containers."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM containers")
    rows = cursor.fetchall()
    cursor.close()
    return [dict(row) for row in rows]

# --- Log CRUD Operations ---
def create_log(log: Log, db: sqlite3.Connection = Depends(get_db)) -> bool:
    """Create a new log entry in the database."""
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO logs (timestamp, userId, actionType, itemId, details)
        VALUES (?, ?, ?, ?, ?)
    """, (log.timestamp, log.userId, log.actionType, log.itemId, log.details))
    db.commit()
    cursor.close()
    return True

def get_logs(item_id: Optional[str] = None, user_id: Optional[str] = None, db: sqlite3.Connection = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve logs, optionally filtered by itemId or userId."""
    cursor = db.cursor()
    query = "SELECT * FROM logs"
    params = []
    if item_id:
        query += " WHERE itemId = ?"
        params.append(item_id)
    elif user_id:
        query += " WHERE userId = ?"
        params.append(user_id)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    return [dict(row) for row in rows]