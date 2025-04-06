# backend/app/api/utils/search.py
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from decimal import Decimal

# Assuming schemas and retrieval_algorithm are available
# from app.schemas import PlacedItem, ItemDefinition
from .retrieval_algorithm import calculate_retrieval_steps

logger = logging.getLogger(__name__)

def calculate_search_score(
    item: 'PlacedItem',
    item_definition: 'ItemDefinition',
    retrieval_steps: int
) -> float:
    """
    Calculates a search score for an item. Lower is better (easier/faster to get).
    Score considers retrieval steps, item priority, and expiry proximity.
    """
    score = 0.0

    # 1. Retrieval Steps (Primary factor)
    # Higher steps means harder to get -> higher score penalty
    score += retrieval_steps * 10.0 # Weight retrieval steps heavily

    # 2. Item Priority (Secondary factor)
    # Lower priority number means HIGHER priority (e.g., 1 is highest)
    # Penalize lower priority items (higher priority number)
    priority = item_definition.priority if item_definition else 5 # Default priority if no definition
    score += priority * 5.0 # Adjust weight as needed

    # 3. Expiry Proximity (Tertiary factor)
    # Penalize items expiring very soon if we DON'T want them now
    # Or reward them if the search implies urgency? Let's penalize for now.
    if item_definition and item_definition.expiryDate:
        try:
            # Ensure expiryDate is offset-aware for comparison
            expiry_dt = item_definition.expiryDate
            if expiry_dt.tzinfo is None:
                 # Assume UTC if timezone info is missing (adjust if needed)
                 expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)

            now_dt = datetime.now(timezone.utc)
            time_to_expiry = expiry_dt - now_dt
            days_to_expiry = time_to_expiry.total_seconds() / (60 * 60 * 24)

            if days_to_expiry < 0:
                score += 1000.0 # Heavily penalize already expired
            elif days_to_expiry < 7:
                score += (7 - days_to_expiry) * 2.0 # Minor penalty for expiring soon
        except Exception as e:
            logger.warning(f"Could not parse expiry date for scoring item {item.id}: {e}")

    # logger.debug(f"Item {item.id}: Steps={retrieval_steps}, Prio={priority}, Score={score}")
    return score

def search_items(
    all_placed_items: List['PlacedItem'], # Flat list of all placed items
    all_definitions: Dict[int, 'ItemDefinition'], # Map definition_id -> definition
    items_by_container: Dict[str, List['PlacedItem']], # Map container_id -> items for retrieval calc
    all_placed_items_map: Dict[int, 'PlacedItem'], # Map item_id -> item for retrieval calc
    query: Optional[str] = None,
    min_priority: Optional[int] = None,
    max_priority: Optional[int] = None,
    container_id: Optional[int] = None,
    expires_before: Optional[datetime] = None,
    expires_after: Optional[datetime] = None,
    sort_by_score: bool = True
) -> List[Dict]:
    """
    Searches for items based on criteria and calculates retrieval steps and score.
    """
    results = []
    # Ensure timezone awareness for comparisons if provided
    if expires_before and expires_before.tzinfo is None:
        expires_before = expires_before.replace(tzinfo=timezone.utc)
    if expires_after and expires_after.tzinfo is None:
        expires_after = expires_after.replace(tzinfo=timezone.utc)

    # *** Optimization: If filtering significantly reduces the item list,
    # apply filters *before* calculating retrieval steps. ***
    # However, calculating steps requires the context of *all* items in the container.

    logger.info(f"Starting search with {len(all_placed_items)} items. Query: '{query}', Container: {container_id}, Prio: {min_priority}-{max_priority}")

    for item in all_placed_items:
        # Get item definition
        definition = all_definitions.get(item.item_definition_id)
        if not definition:
            logger.warning(f"Item definition {item.item_definition_id} not found for placed item {item.id}")
            continue # Skip items without definitions if necessary for filtering

        # --- Apply Filters ---
        if query and query.lower() not in definition.name.lower():
            continue
        if container_id is not None and item.container_id != container_id:
            continue
        if min_priority is not None and definition.priority < min_priority:
            continue
        if max_priority is not None and definition.priority > max_priority:
            continue

        # Date Filtering (handle timezone)
        item_expiry_dt = definition.expiryDate
        if item_expiry_dt and item_expiry_dt.tzinfo is None:
             item_expiry_dt = item_expiry_dt.replace(tzinfo=timezone.utc) # Assume UTC

        if expires_before and (not item_expiry_dt or item_expiry_dt >= expires_before):
            continue
        if expires_after and (not item_expiry_dt or item_expiry_dt <= expires_after):
             continue

        # --- Calculate Steps and Score ---
        logger.debug(f"Calculating steps for filtered item {item.id}")
        # This is the most expensive part
        retrieval_steps = calculate_retrieval_steps(item.id, all_placed_items_map, items_by_container)

        score = calculate_search_score(item, definition, retrieval_steps)

        results.append({
            "placed_item_id": item.id,
            "item_name": definition.name,
            "item_definition_id": item.item_definition_id,
            "container_id": item.container_id,
            "pos_x": item.pos_x,
            "pos_y": item.pos_y,
            "pos_z": item.pos_z,
            "priority": definition.priority,
            "expiry_date": definition.expiryDate,
            "retrieval_steps": retrieval_steps,
            "search_score": score,
            # Include other relevant fields from PlacedItem or ItemDefinition
        })

    # --- Sort Results ---
    if sort_by_score:
        results.sort(key=lambda r: r['search_score'])

    logger.info(f"Search complete. Found {len(results)} items.")
    return results