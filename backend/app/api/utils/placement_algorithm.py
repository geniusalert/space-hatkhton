import sqlite3
from typing import List, Dict, Optional
from ..schemas import Item, Container

def get_db_connection():
    conn = sqlite3.connect("cargo.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_container_items(container_id: str) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE containerId = ?", (container_id,))
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

def overlaps(start1: tuple, end1: tuple, start2: tuple, end2: tuple) -> bool:
    return (start1[0] < end2[0] and end1[0] > start2[0] and
            start1[1] < end2[1] and end1[1] > start2[1] and
            start1[2] < end2[2] and end1[2] > start2[2])

def find_position_in_container(item: Item, container: Container, existing_items: List[Dict]) -> Optional[Dict]:
    for w in range(int(container.width - item.width + 1)):
        for d in range(int(container.depth - item.depth + 1)):
            for h in range(int(container.height - item.height + 1)):
                start = (w, d, h)
                end = (w + item.width, d + item.depth, h + item.height)
                if not any(overlaps(start, end, (ei["startW"], ei["startD"], ei["startH"]), 
                                   (ei["endW"], ei["endD"], ei["endH"])) for ei in existing_items):
                    return {"startCoordinates": start, "endCoordinates": end}
    return None

def place_items(items: List[Item], containers: List[Container]) -> List[Dict]:
    items.sort(key=lambda x: (-x.priority, -(x.width * x.depth * x.height)))
    placements = []
    rearrangements = []

    for item in items:
        placed = False
        preferred_containers = [c for c in containers if c.zone == item.preferredZone]
        all_containers = preferred_containers + [c for c in containers if c not in preferred_containers]

        for container in all_containers:
            existing_items = get_container_items(container.containerId)
            position = find_position_in_container(item, container, existing_items)
            if position:
                item.containerId = container.containerId
                item.startW, item.startD, item.startH = position["startCoordinates"]
                item.endW, item.endD, item.endH = position["endCoordinates"]
                placements.append({
                    "itemId": item.itemId,
                    "containerId": container.containerId,
                    "position": position
                })
                placed = True
                break

        if not placed:
            # Try rearranging low-priority items
            for container in all_containers:
                existing_items = get_container_items(container.containerId)
                low_priority_items = sorted(
                    [i for i in existing_items if i["priority"] < item.priority],
                    key=lambda x: x["priority"]
                )
                for low_item in low_priority_items:
                    for other_container in all_containers:
                        if other_container.containerId != container.containerId:
                            other_items = get_container_items(other_container.containerId)
                            new_pos = find_position_in_container(
                                Item(**{k: low_item[k] for k in low_item}), other_container, other_items
                            )
                            if new_pos:
                                rearrangements.append({
                                    "itemId": low_item["itemId"],
                                    "fromContainer": container.containerId,
                                    "toContainer": other_container.containerId,
                                    "newPosition": new_pos
                                })
                                existing_items = [i for i in existing_items if i["itemId"] != low_item["itemId"]]
                                position = find_position_in_container(item, container, existing_items)
                                if position:
                                    item.containerId = container.containerId
                                    item.startW, item.startD, item.startH = position["startCoordinates"]
                                    item.endW, item.endD, item.endH = position["endCoordinates"]
                                    placements.append({
                                        "itemId": item.itemId,
                                        "containerId": container.containerId,
                                        "position": position
                                    })
                                    placed = True
                                    break
                    if placed:
                        break
                if placed:
                    break

        if not placed:
            raise ValueError(f"Could not place item {item.itemId} even after rearrangement.")

    return {"placements": placements, "rearrangements": rearrangements}