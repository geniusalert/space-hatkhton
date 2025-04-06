# backend/app/api/utils/placement_algorithm.py
import logging
from typing import List, Optional, Dict, Tuple
from decimal import Decimal # Use Decimal for precision if needed, otherwise float is fine

# Assuming schemas are defined elsewhere (e.g., app.schemas)
# from app.schemas import ItemCreate, PlacedItem, Container, ItemDefinition

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def get_item_dimensions(item: 'ItemCreate', rotation: int = 0) -> Tuple[float, float, float]:
    """Gets item dimensions based on rotation (0=XYZ, 1=YXZ, 2=XZY, etc.)."""
    # This needs to be implemented based on your ItemDefinition/ItemCreate schema
    # Example:
    # definition = get_item_definition(item.itemDefinitionId) # Fetch from DB or cache
    # w, h, d = definition.width, definition.height, definition.depth
    # Placeholder dimensions:
    w, h, d = float(item.width), float(item.height), float(item.depth)

    # Simple rotation logic (adjust based on actual rotation rules)
    if rotation == 0: # XYZ (Original)
        return w, h, d
    elif rotation == 1: # YXZ
        return h, w, d
    elif rotation == 2: # XZY
        return w, d, h
    # Add other rotation cases as needed
    else: # Default to original if rotation is unknown
        return w, h, d

def get_item_rotations(item: 'ItemCreate') -> List[int]:
    """Returns a list of valid rotation indices (e.g., 0, 1, 2)."""
    # Return allowed rotations, maybe based on item properties
    return [0, 1, 2] # Example: Allow 3 basic rotations

def check_collision(
    pos_x: float, pos_y: float, pos_z: float,
    dim_w: float, dim_h: float, dim_d: float,
    other_item: 'PlacedItem'
) -> bool:
    """Checks if the new item collides with an existing item."""
    # Basic Axis-Aligned Bounding Box (AABB) collision detection
    # Assumes other_item has position (px, py, pz) and dimensions (pw, ph, pd)
    other_x, other_y, other_z = float(other_item.pos_x), float(other_item.pos_y), float(other_item.pos_z)
    other_w, other_h, other_d = float(other_item.width), float(other_item.height), float(other_item.depth)

    collides_x = (pos_x < other_x + other_w) and (pos_x + dim_w > other_x)
    collides_y = (pos_y < other_y + other_h) and (pos_y + dim_h > other_y)
    collides_z = (pos_z < other_z + other_d) and (pos_z + dim_d > other_z)

    return collides_x and collides_y and collides_z

def is_placement_valid(
    container: 'Container',
    existing_items: List['PlacedItem'],
    pos_x: float, pos_y: float, pos_z: float,
    dim_w: float, dim_h: float, dim_d: float
) -> bool:
    """Checks if placing an item at (x,y,z) with dimensions (w,h,d) is valid."""
    cont_w, cont_h, cont_d = float(container.width), float(container.height), float(container.depth)

    # 1. Check bounds
    if not (0 <= pos_x and pos_x + dim_w <= cont_w and
            0 <= pos_y and pos_y + dim_h <= cont_h and
            0 <= pos_z and pos_z + dim_d <= cont_d):
        # logger.debug(f"Placement invalid: Out of bounds ({pos_x},{pos_y},{pos_z}) D({dim_w},{dim_h},{dim_d}) in C({cont_w},{cont_h},{cont_d})")
        return False

    # 2. Check collisions with existing items
    # *** EFFICIENCY BOTTLENECK ***
    # Iterating through all items is O(N).
    # Replace this loop with a spatial index query (e.g., Octree) for O(log N) or better.
    # spatial_index.query_region(bounding_box_of_new_item) -> potential colliders
    for other_item in existing_items:
        if check_collision(pos_x, pos_y, pos_z, dim_w, dim_h, dim_d, other_item):
            # logger.debug(f"Placement invalid: Collision with item {other_item.item_id} at ({pos_x},{pos_y},{pos_z})")
            return False

    # 3. Check stability (optional, basic check: is it resting on the floor or another item?)
    # Requires more complex geometry checks - omitted for simplicity here.
    # Could check if pos_z == 0 or if the area below the item intersects with another item.

    return True

def get_placement_points(container: 'Container', existing_items: List['PlacedItem'], item_dims: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
    """
    Generates potential placement points.
    Improvement: Instead of fixed grid, try corners of existing items or surfaces.
    This is a simplified placeholder using a grid approach.
    A Maximal Empty Space algorithm would be more robust here.
    """
    points = []
    step = 5.0 # Granularity of placement grid - adjust as needed

    cont_w, cont_h, cont_d = float(container.width), float(container.height), float(container.depth)
    item_w, item_h, item_d = item_dims

    # Basic grid approach (can be inefficient)
    z = 0.0
    while z <= cont_d - item_d:
        y = 0.0
        while y <= cont_h - item_h:
            x = 0.0
            while x <= cont_w - item_w:
                points.append((x, y, z))
                x += step
            y += step
        z += step

    # Add points based on existing item surfaces (simple version)
    for item in existing_items:
        ix, iy, iz = float(item.pos_x), float(item.pos_y), float(item.pos_z)
        iw, ih, _ = float(item.width), float(item.height), float(item.depth) # Assuming depth alignment needed for 'on top'
        # Point on top of existing item
        points.append((ix, iy, iz + float(item.depth)))
        # Points adjacent in x/y (simplified)
        points.append((ix + iw, iy, iz))
        points.append((ix, iy + ih, iz))


    # Deduplicate and return valid starting points (must be within bounds)
    valid_points = []
    seen = set()
    for p in points:
        px, py, pz = p
        if 0 <= px < cont_w and 0 <= py < cont_h and 0 <= pz < cont_d:
             # Check if point itself is inside another item (crude check)
             is_inside = False
             # *** Optimization needed here too if many items ***
             # for other in existing_items:
             #    if check_collision(px, py, pz, 0.1, 0.1, 0.1, other): # Check tiny cube
             #       is_inside = True
             #       break
             if not is_inside and p not in seen:
                 valid_points.append(p)
                 seen.add(p)

    # Sort points (e.g., prioritize lower Z, then Y, then X)
    valid_points.sort(key=lambda p: (p[2], p[1], p[0]))
    return valid_points


def score_placement(
    container: 'Container',
    item: 'ItemCreate',
    pos_x: float, pos_y: float, pos_z: float,
    dim_d: float # Depth dimension for accessibility check
) -> float:
    """
    Scores a potential placement. Lower score is better.
    Improved Score: Includes distance penalty, zone penalty, and basic accessibility penalty.
    """
    score = 0.0
    cont_w, cont_h, cont_d = float(container.width), float(container.height), float(container.depth)

    # 1. Distance Penalty (Prefer closer to origin/access point 0,0,0)
    distance = (pos_x**2 + pos_y**2 + pos_z**2)**0.5
    score += distance * 0.1 # Weight distance less heavily

    # 2. Preferred Zone Penalty
    if item.preferredZone and container.zone != item.preferredZone:
        score += 100.0 # High penalty for wrong zone

    # 3. Accessibility Penalty (Simple: distance from container front)
    # Assumes access is from Z=0 face. Lower Z is better.
    # More advanced: Estimate blocking items (costly here, better done at retrieval)
    accessibility_penalty = pos_z + dim_d # Penalize based on how deep it is
    score += accessibility_penalty * 0.5 # Weight accessibility

    # 4. Stability Score (Optional, complex)
    # score += calculate_stability(...)

    return score

# --- Main Placement Function ---

def find_best_placement_for_item(
    item: 'ItemCreate',
    containers: List['Container'],
    all_placed_items: Dict[str, List['PlacedItem']] # Dict[container_id, list_of_items]
) -> Optional[Dict]:
    """
    Finds the best valid placement for a single item across multiple containers.
    Implements a Best Fit approach combined with scoring.
    """
    best_placement = None
    lowest_score = float('inf')

    valid_containers = [c for c in containers if not item.preferredZone or c.zone == item.preferredZone]
    if not valid_containers:
         valid_containers = containers # Fallback if preferred zone not available

    # Sort containers (optional, e.g., by available space heuristic if calculated)
    # valid_containers.sort(key=lambda c: calculate_available_space(c), reverse=True)

    for container in valid_containers:
        container_id_str = str(container.id) # Ensure key is string if dict expects strings
        existing_items = all_placed_items.get(container_id_str, [])
        logger.debug(f"Checking container {container.id} (Zone: {container.zone}) with {len(existing_items)} items for item {item.name}")

        # *** Optimization: Pre-build spatial index for existing_items here ***
        # spatial_index = build_octree(existing_items)

        for rotation in get_item_rotations(item):
            item_w, item_h, item_d = get_item_dimensions(item, rotation)

            # Get potential starting points
            potential_points = get_placement_points(container, existing_items, (item_w, item_h, item_d))
            logger.debug(f"Container {container.id}, Rotation {rotation}: Found {len(potential_points)} potential points.")

            for point in potential_points:
                pos_x, pos_y, pos_z = point

                # Check if this placement is valid (bounds and collision)
                # Pass spatial_index if using one: is_placement_valid(..., spatial_index=spatial_index)
                if is_placement_valid(container, existing_items, pos_x, pos_y, pos_z, item_w, item_h, item_d):
                    # Calculate score for this valid placement
                    current_score = score_placement(container, item, pos_x, pos_y, pos_z, item_d)
                    logger.debug(f"Valid placement found at {point} in C{container.id}, Rot {rotation}. Score: {current_score}")

                    # Best Fit Heuristic: If valid, keep the one with the lowest score found so far
                    if current_score < lowest_score:
                        lowest_score = current_score
                        best_placement = {
                            "container_id": container.id,
                            "pos_x": pos_x,
                            "pos_y": pos_y,
                            "pos_z": pos_z,
                            "rotation": rotation,
                            "placed_width": item_w, # Store actual dimensions used
                            "placed_height": item_h,
                            "placed_depth": item_d,
                            "score": current_score,
                        }
                        logger.info(f"New best placement found for item {item.name}: Score {current_score} in C{container.id}")

                    # Original code's optimization (commented out): stop if any placement found in preferred zone
                    # This is generally NOT Best Fit, but First Fit within preferred zone.
                    # Keep searching for the lowest score across all valid spots.
                    # if container.zone == item.preferredZone:
                    #    logger.debug("Stopping search for this container (found spot in preferred zone).")
                    #    # This break is for the points loop. Might need another flag to break container loop.
                    #    break # Consider if this early exit is desirable vs finding the absolute best score

            # If a placement was found in this container, no need to check other rotations for this container *if*
            # the goal is just *any* placement. But for *best* placement, we must check all rotations.

    if best_placement:
        logger.info(f"Final best placement for item {item.name}: Score {best_placement['score']} in C{best_placement['container_id']}")
    else:
        logger.warning(f"Could not find any valid placement for item {item.name} (ID: {item.itemDefinitionId})")

    return best_placement