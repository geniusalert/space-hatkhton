import sqlite3
from typing import List, Dict, Optional
from ..schemas import Item, Container

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect("cargo.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_container_items(container_id: str) -> List[Dict]:
    """Retrieve all items currently in a container from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE containerId = ?", (container_id,))
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

def place_items(items: List[Item], containers: List[Container]) -> List[Dict]:
    """
    Place items into containers using a 3D bin packing approach.
    - Sort items by priority (descending) and volume (descending).
    - Respect preferred zones when possible.
    - Return placement details with coordinates.
    """
    # Sort items by priority (desc) and then by volume (desc)
    items.sort(key=lambda x: (-x.priority, -(x.width * x.depth * x.height)))
    
    placements = []
    
    for item in items:
        placed = False
        # Prioritize containers in the item's preferred zone
        preferred_containers = [c for c in containers if c.zone == item.preferredZone]
        # Fallback to all containers if preferred zone fails
        for container in preferred_containers + [c for c in containers if c not in preferred_containers]:
            position = find_position_in_container(item, container)
            if position:
                placements.append({
                    "itemId": item.itemId,
                    "containerId": container.containerId,
                    "position": position
                })
                # Update item with placement details
                item.containerId = container.containerId
                item.startW, item.startD, item.startH = position["startCoordinates"]
                item.endW, item.endD, item.endH = position["endCoordinates"]
                placed = True
                break
        if not placed:
            raise ValueError(f"Could not place item {item.itemId} in any container.")
    
    return placements

def find_position_in_container(item: Item, container: Container) -> Optional[Dict]:
    """
    Find a valid position for the item in the container without overlaps.
    - Check all possible positions in the 3D grid.
    - Return start and end coordinates if a spot is found.
    """
    existing_items = get_container_items(container.containerId)
    
    # Iterate through possible positions in the container
    for w in range(int(container.width - item.width + 1)):
        for d in range(int(container.depth - item.depth + 1)):
            for h in range(int(container.height - item.height + 1)):
                start = (w, d, h)
                end = (w + item.width, d + item.depth, h + item.height)
                # Check for overlaps with existing items
                if not any(overlaps(start, end, (ei["startW"], ei["startD"], ei["startH"]), 
                                   (ei["endW"], ei["endD"], ei["endH"])) for ei in existing_items):
                    return {
                        "startCoordinates": start,
                        "endCoordinates": end
                    }
    return None

def overlaps(start1: tuple, end1: tuple, start2: tuple, end2: tuple) -> bool:
    """Check if two 3D boxes overlap in space."""
    return (start1[0] < end2[0] and end1[0] > start2[0] and
            start1[1] < end2[1] and end1[1] > start2[1] and
            start1[2] < end2[2] and end1[2] > start2[2])