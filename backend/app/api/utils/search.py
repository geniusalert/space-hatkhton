from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from ..crud import get_item_by_id, get_item_by_name, get_container, get_container_items
from ..utils.retrieval_algorithm import calculate_retrieval_steps

router = APIRouter()

@router.get("/api/search")
async def search_item(
    itemId: Optional[str] = Query(None, description="Unique ID of the item"),
    itemName: Optional[str] = Query(None, description="Name of the item"),
    userId: Optional[str] = Query(None, description="ID of the user making the request")
):
    """
    Search for an item by ID or name and return its details along with retrieval steps.

    - **itemId**: The unique identifier of the item (optional).
    - **itemName**: The name of the item (optional).
    - **userId**: The ID of the user (optional, for logging purposes).
    - Returns: A JSON response with success status, found status, and item details if found.
    """
    # Ensure at least one search parameter is provided
    if not itemId and not itemName:
        raise HTTPException(status_code=400, detail="Either itemId or itemName must be provided")

    # Fetch the item from the database
    item: Dict = None
    if itemId:
        item = get_item_by_id(itemId)
    else:
        item = get_item_by_name(itemName)  # Assumes this returns the first match

    # Handle case where item is not found
    if not item:
        return {"success": True, "found": False}

    # Get container details to determine the zone
    container = get_container(item["containerId"])
    zone = container["zone"] if container else "Unknown"

    # Get all items in the same container for retrieval step calculation
    container_items: List[Dict] = get_container_items(item["containerId"])

    # Calculate retrieval steps using the retrieval algorithm
    steps: List[Dict] = calculate_retrieval_steps(item, container_items)

    # Construct the response
    response_item = {
        "itemId": item["itemId"],
        "name": item["name"],
        "containerId": item["containerId"],
        "zone": zone,
        "position": {
            "startCoordinates": {
                "width": item["startW"],
                "depth": item["startD"],
                "height": item["startH"]
            },
            "endCoordinates": {
                "width": item["endW"],
                "depth": item["endD"],
                "height": item["endH"]
            }
        },
        "retrievalSteps": steps
    }

    return {"success": True, "found": True, "item": response_item}