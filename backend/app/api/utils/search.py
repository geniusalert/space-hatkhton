# backend/app/api/search.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date

# Adjust imports based on your project structure
from app import crud, schemas
from app.database import SessionLocal
from app.api.utils.retrieval_algorithm import calculate_retrieval_steps, get_blocking_items

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_days_to_expiry(expiry_date_str: Optional[str]) -> float:
    """Calculates days until expiry. Returns infinity if no date or invalid."""
    if not expiry_date_str:
        return float('inf')
    try:
        # Assuming expiry_date_str is in 'YYYY-MM-DD' format
        expiry_date = date.fromisoformat(expiry_date_str)
        today = date.today()
        delta = expiry_date - today
        return float(delta.days)
    except (ValueError, TypeError):
        # Handle invalid date format or None
        return float('inf')

def calculate_search_score(retrieval_steps: int, days_to_expiry: float) -> float:
    """
    Calculates a score for prioritizing retrieval. Lower is better.
    Prioritizes fewer steps, then closer expiry date.
    """
    # Main priority: fewer steps
    score = float(retrieval_steps)

    # Secondary priority: Closer expiry (fewer days left)
    # Add a small component for days_to_expiry.
    # Ensure items expiring sooner get a slightly lower score.
    # If days_to_expiry is large (far future or no expiry), it adds less penalty.
    # If days_to_expiry is small (or negative -> past expiry), it adds more penalty (or slight bonus).
    # We clamp positive days to avoid excessively penalizing far-future items.
    # A simple approach: add a fraction of days, capped.
    expiry_penalty = 0.0
    if days_to_expiry != float('inf'):
        # Give a slight advantage to items expiring sooner (lower days_to_expiry)
        # Normalize or scale this value based on typical expiry ranges if needed
        expiry_penalty = max(0, days_to_expiry) / 100.0 # Example scaling: divide by 100

    score += expiry_penalty

    # Consider priority as well? (Example - uncomment and adjust if needed)
    # lower priority number means higher actual priority
    # score += (item_priority / 10.0) # Add small penalty for lower priority items

    return score


@router.get("/search", response_model=schemas.SearchResponse) # Assuming a SearchResponse schema exists
async def search_item(
    itemName: Optional[str] = Query(None, description="Name of the item to search for"),
    itemId: Optional[str] = Query(None, description="Exact ID of the item to search for"),
    userId: str = Query(..., description="ID of the user performing the search (for logging)"),
    db: Session = Depends(get_db)
):
    """
    Searches for an item by ID or Name.
    - If ID is provided, returns that specific item's location and retrieval info.
    - If Name is provided, finds all items with that name and returns the one
      that is optimal to retrieve (fewest steps, closest expiry).
    """
    if not itemId and not itemName:
        raise HTTPException(status_code=400, detail="Please provide either itemId or itemName.")
    if itemId and itemName:
        raise HTTPException(status_code=400, detail="Provide either itemId or itemName, not both.")

    search_results = []
    best_item_details = None
    min_score = float('inf')

    # Fetch all placed items once for efficient lookup if searching by name
    all_placed_items_db = crud.get_all_placed_items(db) # Ensure this CRUD function exists
    all_placed_items_map: Dict[str, List[schemas.PlacedItem]] = {}
    for item in all_placed_items_db:
        if item.containerId not in all_placed_items_map:
            all_placed_items_map[item.containerId] = []
        # Convert DB model to Pydantic schema if necessary, assuming crud returns Pydantic models
        all_placed_items_map[item.containerId].append(schemas.PlacedItem.model_validate(item))


    if itemId:
        # --- Search by Specific ID ---
        target_item_db = crud.get_placed_item_by_id(db, item_id=itemId) # Ensure this CRUD exists
        if not target_item_db:
            raise HTTPException(status_code=404, detail=f"Item with ID '{itemId}' not found.")

        # Convert to Pydantic schema
        target_item = schemas.PlacedItem.model_validate(target_item_db)

        # Get items in the same container
        items_in_container = all_placed_items_map.get(target_item.containerId, [])

        # Calculate retrieval steps
        blocking_items_info = get_blocking_items(target_item, items_in_container)
        retrieval_steps = len(blocking_items_info)
        retrieval_instructions = [{"move": item.itemId, "from": item.containerId} for item in blocking_items_info]

        # Log the search action (implement crud.create_log if needed)
        # crud.create_log(db, schemas.LogCreate(userId=userId, action=f"Searched by ID: {itemId}", details=f"Found in {target_item.containerId}. Steps: {retrieval_steps}"))

        search_results.append(schemas.SearchResultItem( # Assuming this schema exists
             item=target_item,
             retrieval_steps=retrieval_steps,
             blocking_items=[b.itemId for b in blocking_items_info],
             retrieval_instructions=retrieval_instructions
         ))
        best_item_details = search_results[0] # Only one result when searching by ID


    elif itemName:
        # --- Search by Name ---
        found_items_db = crud.get_placed_items_by_name(db, item_name=itemName) # Ensure this CRUD exists
        if not found_items_db:
             raise HTTPException(status_code=404, detail=f"No items found with name '{itemName}'.")

        # Log the search action
        # crud.create_log(db, schemas.LogCreate(userId=userId, action=f"Searched by Name: {itemName}", details=f"Found {len(found_items_db)} potential matches."))

        for item_db in found_items_db:
            item = schemas.PlacedItem.model_validate(item_db) # Convert to Pydantic

            # Get items in the same container
            items_in_container = all_placed_items_map.get(item.containerId, [])

            # Calculate retrieval steps for this specific item instance
            blocking_items_info = get_blocking_items(item, items_in_container)
            retrieval_steps = len(blocking_items_info)

            # Get original item details to fetch expiry date (assuming PlacedItem doesn't store it)
            original_item_details = crud.get_item_definition(db, item_id=item.itemId) # Assumes a function to get the original item definition
            days_to_expiry = calculate_days_to_expiry(original_item_details.expiryDate if original_item_details else None)

            # Calculate score
            score = calculate_search_score(retrieval_steps, days_to_expiry) # Add item.priority if needed

            # Check if this item is better than the current best
            if score < min_score:
                min_score = score
                retrieval_instructions = [{"move": b.itemId, "from": b.containerId} for b in blocking_items_info]
                best_item_details = schemas.SearchResultItem(
                     item=item,
                     retrieval_steps=retrieval_steps,
                     blocking_items=[b.itemId for b in blocking_items_info],
                     retrieval_instructions=retrieval_instructions,
                     score=score # Optional: include score in response for debugging/info
                )
                # print(f"New best: ID={item.itemId}, Steps={retrieval_steps}, ExpiryDays={days_to_expiry:.1f}, Score={score:.2f}")


    if not best_item_details:
         # This case should ideally not be reached if checks above are correct, but as a fallback
         raise HTTPException(status_code=404, detail="No suitable item found matching criteria.")

    # Return the single best result
    return schemas.SearchResponse(results=[best_item_details])