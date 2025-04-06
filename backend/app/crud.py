import sqlite3
from typing import Optional, List, Dict, Any
from .schemas import Item, Container, Log  # Importing Pydantic models

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect("cargo.db")
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

# --- Item CRUD Operations ---
def create_item(item: Item) -> bool:
    """Create a new item in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO items (itemId, name, width, depth, height, mass, priority, expiryDate, usageLimit, preferredZone, 
                              containerId, startW, startD, startH, endW, endD, endH)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item.itemId, item.name, item.width, item.depth, item.height, item.mass, item.priority, item.expiryDate,
              item.usageLimit, item.preferredZone, item.containerId, item.startW, item.startD, item.startH,
              item.endW, item.endD, item.endH))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Duplicate itemId
    finally:
        conn.close()

def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an item by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE itemId = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_item(item_id: str, updates: Dict[str, Any]) -> bool:
    """Update an existing item's fields."""
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
    values = list(updates.values()) + [item_id]
    cursor.execute(f"UPDATE items SET {set_clause} WHERE itemId = ?", values)
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def delete_item(item_id: str) -> bool:
    """Delete an item by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE itemId = ?", (item_id,))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

# --- Container CRUD Operations ---
def create_container(container: Container) -> bool:
    """Create a new container in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO containers (containerId, zone, width, depth, height)
            VALUES (?, ?, ?, ?, ?)
        """, (container.containerId, container.zone, container.width, container.depth, container.height))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Duplicate containerId
    finally:
        conn.close()

def get_container(container_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a container by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM containers WHERE containerId = ?", (container_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_containers() -> List[Dict[str, Any]]:
    """Retrieve all containers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM containers")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Log CRUD Operations ---
def create_log(log: Log) -> bool:
    """Create a new log entry in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (timestamp, userId, actionType, itemId, details)
        VALUES (?, ?, ?, ?, ?)
    """, (log.timestamp, log.userId, log.actionType, log.itemId, log.details))
    conn.commit()
    conn.close()
    return True

def get_logs(item_id: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve logs, optionally filtered by itemId or userId."""
    conn = get_db_connection()
    cursor = conn.cursor()
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
    conn.close()
    return [dict(row) for row in rows]