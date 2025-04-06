# backend/app/api/utils/placement_algorithm.py

from typing import List, Optional, Tuple
# Assuming schemas.py defines these classes (adapt imports if structure differs)
# from app.schemas import ItemCreate, Container, PlacedItem
# Make sure these schemas have the necessary attributes (dimensions, coordinates etc.)

# Placeholder schemas if not imported - replace with your actual schemas
class ItemCreate:
    def __init__(self, itemId: str, name: str, width: float, depth: float, height: float, mass: float, priority: int, expiryDate: str, usageLimit: int, preferredZone: Optional[str] = None):
        self.itemId = itemId
        self.name = name
        self.width = width
        self.depth = depth
        self.height = height
        self.mass = mass
        self.priority = priority
        self.expiryDate = expiryDate
        self.usageLimit = usageLimit
        self.preferredZone = preferredZone

class Container:
     def __init__(self, containerId: str, zone: str, width: float, depth: float, height: float):
         self.containerId = containerId
         self.zone = zone
         self.width = width
         self.depth = depth
         self.height = height

class PlacedItem:
    def __init__(self, itemId: str, name: str, containerId: str, startW: float, startD: float, startH: float, width: float, depth: float, height: float, priority: int):
        self.itemId = itemId
        self.name = name
        self.containerId = containerId
        self.startW = startW
        self.startD = startD
        self.startH = startH
        self.width = width
        self.depth = depth
        self.height = height
        self.priority = priority # Added priority for potential scoring use

# --- Helper Functions ---

def get_item_rotations(item: ItemCreate) -> List[Tuple[float, float, float]]:
    """Generates all 6 possible rotations for an item's dimensions."""
    w, d, h = item.width, item.depth, item.height
    return [
        (w, d, h), (w, h, d),
        (d, w, h), (d, h, w),
        (h, w, d), (h, d, w)
    ]

def overlaps(
    item1_pos: Tuple[float, float, float], item1_dims: Tuple[float, float, float],
    item2_pos: Tuple[float, float, float], item2_dims: Tuple[float, float, float]
) -> bool:
    """Checks if two 3D cuboids overlap."""
    sW1, sD1, sH1 = item1_pos
    w1, d1, h1 = item1_dims
    sW2, sD2, sH2 = item2_pos
    w2, d2, h2 = item2_dims

    # Check for non-overlap along each axis
    x_overlap = (sW1 < sW2 + w2) and (sW1 + w1 > sW2)
    y_overlap = (sD1 < sD2 + d2) and (sD1 + d1 > sD2) # Changed variable name for clarity
    z_overlap = (sH1 < sH2 + h2) and (sH1 + h1 > sH2) # Changed variable name for clarity

    return x_overlap and y_overlap and z_overlap

def check_placement_validity(
    placement_pos: Tuple[float, float, float],
    item_dims: Tuple[float, float, float],
    container: Container,
    existing_items: List[PlacedItem]
) -> bool:
    """Checks if placing item_dims at placement_pos is valid."""
    sW, sD, sH = placement_pos
    w, d, h = item_dims

    # 1. Check container boundaries
    if not (0 <= sW and sW + w <= container.width and
            0 <= sD and sD + d <= container.depth and
            0 <= sH and sH + h <= container.height):
        # print(f"Boundary check failed: pos=({sW},{sD},{sH}), dim=({w},{d},{h}), cont=({container.width},{container.depth},{container.height})")
        return False

    # 2. Check overlap with existing items
    for existing in existing_items:
        existing_pos = (existing.startW, existing.startD, existing.startH)
        existing_dims = (existing.width, existing.depth, existing.height)
        if overlaps(placement_pos, item_dims, existing_pos, existing_dims):
            # print(f"Overlap detected with {existing.itemId}")
            return False

    # 3. (Optional) Check for stable placement (item base fully supported)
    # This adds complexity - basic check assumes placement is stable if it doesn't overlap
    # A more complex check would verify the area below the item is occupied or is the container floor.

    return True

def generate_placement_points(container: Container, existing_items: List[PlacedItem]) -> List[Tuple[float, float, float]]:
    """Generates potential stable points to try placing a new item."""
    points = set([(0.0, 0.0, 0.0)]) # Start with the origin

    # Add points based on corners of existing items
    for item in existing_items:
        # Points on top of the item (potential base for next item)
        points.add((item.startW, item.startD, item.startH + item.height))
        # Points adjacent in width
        points.add((item.startW + item.width, item.startD, item.startH))
        # Points adjacent in depth
        points.add((item.startW, item.startD + item.depth, item.startH))

        # Also consider corners relative to container boundaries (less crucial if iterating based on item corners)
        # points.add((item.startW + item.width, item.startD, 0)) # Project to floor
        # points.add((item.startW, item.startD + item.depth, 0)) # Project to floor

    # Refine points: Remove points clearly outside container (though check_placement_validity handles this too)
    refined_points = {
        p for p in points if
        0 <= p[0] < container.width and
        0 <= p[1] < container.depth and
        0 <= p[2] < container.height
    }

    # Sort points: Prioritize lower depth (D), then lower width (W), then lower height (H)
    # This aims for placements closer to the front, bottom-left
    sorted_points = sorted(list(refined_points), key=lambda p: (p[1], p[0], p[2]))

    return sorted_points

def calculate_placement_score(
    placement_pos: Tuple[float, float, float],
    item: ItemCreate,
    container: Container,
    is_preferred_zone: bool
) -> float:
    """Calculates a score for a valid placement (lower is better)."""
    sW, sD, sH = placement_pos
    score = 0.0

    # 1. Primary factor: Depth (Accessibility) - Lower depth is much better.
    score += sD * 100 # Weight depth heavily

    # 2. Secondary factor: Height - Lower is generally better.
    score += sH * 10

    # 3. Tertiary factor: Width - Less critical, but keep things packed left.
    score += sW

    # 4. Penalty for not being in preferred zone
    if not is_preferred_zone:
        score += 500 # Significant penalty

    # 5. (Optional) Adjust score based on item priority
    # Example: Penalize placing low-priority items at very accessible spots (low depth)
    # Or reward placing high-priority items at accessible spots.
    # if item.priority < 5 and sD < container.depth / 3:
    #     score += 100 # Penalty for low priority item taking prime spot
    # elif item.priority >= 8 and sD < container.depth / 3:
    #      score -= 50 # Bonus for high priority item accessibility

    return score


# --- Main Placement Logic ---

def find_best_placement_for_item(
    item_to_place: ItemCreate,
    containers: List[Container],
    all_placed_items: List[PlacedItem] # Items currently placed in ALL containers
) -> Optional[Tuple[str, Tuple[float, float, float], Tuple[float, float, float]]]:
    """
    Finds the best placement (containerId, position, dimensions) for a new item.
    Returns None if no suitable placement is found.
    """
    best_placement = None
    min_score = float('inf')

    # Sort containers: Prioritize item's preferred zone, then others
    sorted_containers = sorted(
        containers,
        key=lambda c: 0 if c.zone == item_to_place.preferredZone else 1 if item_to_place.preferredZone else 0
        # If no preferred zone, treat all as equal (priority 0)
    )

    for container in sorted_containers:
        # Get items currently placed ONLY in this specific container
        items_in_this_container = [
            p_item for p_item in all_placed_items if p_item.containerId == container.containerId
        ]

        # Generate candidate starting points for placement in this container
        potential_points = generate_placement_points(container, items_in_this_container)

        is_preferred = (container.zone == item_to_place.preferredZone)

        # Try placing the item at each point with each rotation
        for point in potential_points:
            for item_dims in get_item_rotations(item_to_place):
                # Check if this placement (point + dimension) is valid
                is_valid = check_placement_validity(
                    point, item_dims, container, items_in_this_container
                )

                if is_valid:
                    # Calculate a score for this valid placement
                    score = calculate_placement_score(point, item_to_place, container, is_preferred)

                    # If this placement is better than the current best, update
                    if score < min_score:
                        min_score = score
                        best_placement = (container.containerId, point, item_dims)
                        # print(f"New best placement found: score={score}, container={container.containerId}, pos={point}, dims={item_dims}")

        # Optimization: If a good placement is found in the preferred zone,
        # we might stop early, depending on how crucial optimality vs speed is.
        # For a hackathon, finding *any* placement in the preferred zone might be good enough.
        # if best_placement and is_preferred:
        #      print(f"Placement found in preferred zone {container.zone}. Stopping search.")
        #      break # Or continue searching all containers for the absolute best score

    if best_placement:
        container_id, position, final_dims = best_placement
        print(f"Final Best Placement: Container={container_id}, Position={position}, Dimensions={final_dims}, Score={min_score}")
        return container_id, position, final_dims
    else:
        print(f"Could not find any valid placement for item {item_to_place.itemId}")
        return None

# --- Example Usage (requires creating dummy data or integrating with your app) ---
if __name__ == '__main__':
    # Dummy data for testing - replace with data from your database/API calls
    item1 = ItemCreate(itemId="ITEM001", name="Food Pack", width=10, depth=10, height=5, mass=1, priority=5, expiryDate="2026-12-31", usageLimit=1, preferredZone="ZoneA")
    item2 = ItemCreate(itemId="ITEM002", name="Toolbox", width=30, depth=20, height=15, mass=5, priority=8, expiryDate="2030-01-01", usageLimit=10, preferredZone="ZoneB")
    item_to_place_now = ItemCreate(itemId="ITEM003", name="Sample Kit", width=8, depth=12, height=6, mass=0.5, priority=9, expiryDate="2025-08-01", usageLimit=1, preferredZone="ZoneA")

    container1 = Container(containerId="CONT-A1", zone="ZoneA", width=50, depth=50, height=50)
    container2 = Container(containerId="CONT-B1", zone="ZoneB", width=40, depth=60, height=40)

    # Assume item1 is already placed in container1
    placed_items = [
        PlacedItem(itemId="ITEM001", name="Food Pack", containerId="CONT-A1", startW=0, startD=0, startH=0, width=10, depth=10, height=5, priority=5)
    ]

    all_containers = [container1, container2]

    # Find placement for item_to_place_now
    result = find_best_placement_for_item(item_to_place_now, all_containers, placed_items)

    if result:
        found_container_id, found_pos, found_dims = result
        print(f"\nSuccessfully placed {item_to_place_now.name} in {found_container_id} at {found_pos} with dimensions {found_dims}")
        # Here you would typically add the newly placed item to your 'placed_items' list or database
    else:
        print(f"\nFailed to find placement for {item_to_place_now.name}.")
        # Here you might trigger rearrangement logic if needed