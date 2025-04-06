# backend/app/api/utils/retrieval_algorithm.py
import logging
from typing import List, Set
from decimal import Decimal # Use Decimal for precision if needed

# Assuming schemas are defined elsewhere
# from app.schemas import PlacedItem

logger = logging.getLogger(__name__)

def get_blocking_items(
    target_item: 'PlacedItem',
    items_in_container: List['PlacedItem']
) -> Set[int]:
    """
    Identifies items directly blocking the target item based on a 'straight out' retrieval path.
    Assumes retrieval is along the positive Z axis relative to the item's placed position.
    """
    blocking_items_ids = set()
    target_x, target_y, target_z = float(target_item.pos_x), float(target_item.pos_y), float(target_item.pos_z)
    target_w, target_h, target_d = float(target_item.width), float(target_item.height), float(target_item.depth)

    # Define the retrieval volume/path in front of the target item
    # This volume extends from target_z + target_d outwards along Z.
    retrieval_min_x = target_x
    retrieval_max_x = target_x + target_w
    retrieval_min_y = target_y
    retrieval_max_y = target_y + target_h
    retrieval_start_z = target_z + target_d

    # *** EFFICIENCY BOTTLENECK ***
    # Iterating through all items is O(N).
    # Replace this loop with a spatial index query for the retrieval volume.
    # spatial_index.query_region(retrieval_bounding_box) -> potential blockers

    for other_item in items_in_container:
        if other_item.id == target_item.id:
            continue # Don't check against self

        other_x, other_y, other_z = float(other_item.pos_x), float(other_item.pos_y), float(other_item.pos_z)
        other_w, other_h, other_d = float(other_item.width), float(other_item.height), float(other_item.depth)

        # Check if 'other_item' intersects the retrieval path/volume
        # 1. Is it in front of the target item along the retrieval axis (Z)?
        is_in_front = other_z >= retrieval_start_z

        # 2. Does it overlap in the X-Y plane within the target's width/height?
        overlaps_xy = (max(retrieval_min_x, other_x) < min(retrieval_max_x, other_x + other_w) and
                       max(retrieval_min_y, other_y) < min(retrieval_max_y, other_y + other_h))

        if is_in_front and overlaps_xy:
             # More precise check: Does any part of other_item block the *entire* face?
             # For simplicity here, any overlap in front is considered blocking.
             # A more complex check might be needed depending on exact rules.
            logger.debug(f"Item {other_item.id} blocks target {target_item.id}")
            blocking_items_ids.add(other_item.id)

    return blocking_items_ids


def calculate_retrieval_steps(
    target_item_id: int,
    all_placed_items_map: Dict[int, 'PlacedItem'], # Map item_id -> PlacedItem object
    items_by_container: Dict[str, List['PlacedItem']] # Map container_id -> List[PlacedItem]
) -> int:
    """
    Calculates the number of items that need to be moved to retrieve the target item.
    Uses a recursive approach to find nested blocking items.
    """
    if target_item_id not in all_placed_items_map:
        logger.error(f"Target item ID {target_item_id} not found in placed items map.")
        return float('inf') # Or raise error

    target_item = all_placed_items_map[target_item_id]
    container_id_str = str(target_item.container_id)

    if container_id_str not in items_by_container:
         logger.error(f"Container ID {container_id_str} for item {target_item_id} not found.")
         return float('inf') # Or raise error

    items_in_container = items_by_container[container_id_str]

    # *** Optimization: Pre-build spatial index for items_in_container here if not done globally ***
    # spatial_index = build_octree(items_in_container)
    # direct_blockers = get_blocking_items(target_item, items_in_container, spatial_index)

    items_to_move = set()
    queue = {target_item_id} # Start with the target itself (doesn't count as move, but initiates check)
    processed = set()

    while queue:
        current_item_id = queue.pop()
        if current_item_id in processed:
            continue
        processed.add(current_item_id)

        if current_item_id not in all_placed_items_map:
            logger.warning(f"Item ID {current_item_id} (needed for retrieval path) not found.")
            continue

        current_item = all_placed_items_map[current_item_id]

        # Find items directly blocking the current item
        # Pass spatial_index if available: direct_blockers = get_blocking_items(current_item, items_in_container, spatial_index)
        direct_blockers = get_blocking_items(current_item, items_in_container)

        for blocker_id in direct_blockers:
            if blocker_id not in processed:
                items_to_move.add(blocker_id) # This item needs to be moved
                queue.add(blocker_id) # We need to check what blocks this blocker

    logger.info(f"Retrieval steps for item {target_item_id}: {len(items_to_move)} items need moving: {items_to_move}")
    return len(items_to_move)