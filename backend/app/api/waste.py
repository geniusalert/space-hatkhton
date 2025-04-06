# backend/app/api/waste.py

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

# Adjust imports based on your project structure
from app import crud, schemas
from app.database import SessionLocal

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Helper Function to Identify Waste ---

def identify_waste_items(db: Session) -> List[schemas.WasteItem]:
    """
    Identifies all items considered waste based on expiry date or usage limit.
    Note: Requires ItemDefinition model to have 'expiryDate' and 'usageLimit',
          and PlacedItem model to track current usage if usageLimit is used.
          This example primarily focuses on expiry date.
    """
    waste_items = []
    all_placed = crud.get_all_placed_items(db)
    today = date.today()

    item_definitions_cache = {} # Cache definitions to avoid repeated DB calls

    for placed_item in all_placed:
        is_waste = False
        reason = ""
        days_to_expiry: Optional[float] = None

        # Get item definition details (expiry, usage limit, mass etc.)
        if placed_item.itemId not in item_definitions_cache:
             item_def = crud.get_item_definition(db, item_id=placed_item.itemId)
             if not item_def:
                 # Log warning: Placed item exists without definition?
                 print(f"Warning: Item definition not found for placed item ID {placed_item.itemId}")
                 continue
             item_definitions_cache[placed_item.itemId] = item_def
        else:
            item_def = item_definitions_cache[placed_item.itemId]


        # 1. Check Expiry Date
        if item_def.expiryDate:
            try:
                expiry_date = item_def.expiryDate # Assuming it's already a date object from DB/Schema
                delta = expiry_date - today
                days_to_expiry = float(delta.days)
                if delta.days < 0:
                    is_waste = True
                    reason = f"Expired on {expiry_date.isoformat()}"
            except Exception as e:
                 # Log error parsing date
                 print(f"Error processing expiry date for {item_def.itemId}: {e}")
                 days_to_expiry = None # Mark as unknown

        # 2. Check Usage Limit (requires PlacedItem model to track usage)
        # Example: Assumes PlacedItem has a 'current_usage' field
        # if item_def.usageLimit is not None and hasattr(placed_item, 'current_usage'):
        #    if placed_item.current_usage >= item_def.usageLimit:
        #        if not is_waste: # Avoid duplicating if already expired
        #            is_waste = True
        #            reason = f"Usage limit ({item_def.usageLimit}) reached"
        #        else:
        #            reason += f"; Usage limit ({item_def.usageLimit}) reached"

        if is_waste:
             # Convert PlacedItem DB model to PlacedItem schema
             placed_item_schema = schemas.PlacedItem.model_validate(placed_item)

             # Create WasteItem schema (inherits from PlacedItem)
             waste_item_schema = schemas.WasteItem(
                 **placed_item_schema.model_dump(), # Unpack fields from PlacedItem
                 days_to_expiry=days_to_expiry
                 # Add reason field to WasteItem schema if desired
             )
             waste_items.append(waste_item_schema)

    return waste_items


# --- API Endpoints ---

@router.get("/waste/identify", response_model=List[schemas.WasteItem])
async def get_waste_items(
    userId: str, # For logging
    db: Session = Depends(get_db)
):
    """Identifies and returns a list of all items currently considered waste."""
    waste = identify_waste_items(db)

    # Log the action
    crud.create_log(db, schemas.LogCreate(userId=userId, action="Identify Waste", details=f"Found {len(waste)} waste items."))

    return waste


@router.post("/waste/plan_return", response_model=schemas.WastePlanResponse)
async def plan_waste_return(
    plan_request: schemas.WastePlanRequest,
    db: Session = Depends(get_db)
):
    """
    Identifies waste items and selects an optimal set (maximizing count)
    to move to an undocking container based on a maximum weight constraint,
    using a greedy approach (smallest weight first).
    """
    max_weight = plan_request.max_weight
    target_container_id = plan_request.undocking_container_id
    user_id = plan_request.userId

    # 1. Identify all potential waste items
    all_waste = identify_waste_items(db)

    # 2. Filter out items already in the target container
    candidate_waste = [
        item for item in all_waste if item.containerId != target_container_id
    ]

    if not candidate_waste:
         # Log the action
         crud.create_log(db, schemas.LogCreate(userId=user_id, action="Plan Waste Return", details=f"No waste items found eligible for move to {target_container_id}."))
         return schemas.WastePlanResponse(items_to_move=[], total_items=0, total_weight=0.0)

    # 3. Get mass for each candidate item (requires accessing ItemDefinition)
    candidates_with_mass = []
    item_definitions_cache = {}
    for item in candidate_waste:
         if item.itemId not in item_definitions_cache:
             item_def = crud.get_item_definition(db, item_id=item.itemId)
             if not item_def:
                 print(f"Warning: Item definition not found for waste item ID {item.itemId}")
                 continue
             item_definitions_cache[item.itemId] = item_def
         else:
             item_def = item_definitions_cache[item.itemId]

         candidates_with_mass.append({
             "item": item, # The full WasteItem schema object
             "mass": item_def.mass
         })

    # 4. Sort candidates by mass (ascending) - Greedy approach for max count
    sorted_candidates = sorted(candidates_with_mass, key=lambda x: x["mass"])

    # 5. Select items greedily
    selected_items_for_plan: List[schemas.WastePlanResponseItem] = []
    current_weight = 0.0

    for candidate in sorted_candidates:
        item_mass = candidate["mass"]
        item_data = candidate["item"]

        if current_weight + item_mass <= max_weight:
            selected_items_for_plan.append(schemas.WastePlanResponseItem(
                itemId=item_data.itemId,
                name=item_data.name,
                from_containerId=item_data.containerId,
                mass=item_mass
            ))
            current_weight += item_mass
        else:
            # Since sorted by ascending weight, no heavier item will fit either.
            # If we wanted to maximize *weight* instead of count, we'd need knapsack DP.
            pass # Continue checking smaller items if any remain (though unlikely with this sort)

    # Log the action
    crud.create_log(db, schemas.LogCreate(
        userId=user_id,
        action="Plan Waste Return",
        details=(
            f"Planned move of {len(selected_items_for_plan)} items "
            f"(Total Weight: {current_weight:.2f} / {max_weight:.2f} kg) "
            f"to container {target_container_id}."
        )
    ))

    # 6. Return the plan
    return schemas.WastePlanResponse(
        items_to_move=selected_items_for_plan,
        total_items=len(selected_items_for_plan),
        total_weight=current_weight
    )

