from fastapi import APIRouter, HTTPException
from ..schemas import RetrieveRequest, Log
from ..crud import get_item_by_id, update_item, create_log
import json

router = APIRouter()  # Fixed typo from L=APIRouter()

@router.post("/api/retrieve")
async def retrieve_item(request: RetrieveRequest):
    """
    Retrieve an item, update its usage limit, and log the action.

    - **request**: A JSON body containing itemId, userId, and timestamp.
    - Returns: A JSON response indicating success or failure.
    """
    # Fetch the item from the database
    item = get_item_by_id(request.itemId)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check if the item has remaining uses
    if item["usageLimit"] <= 0:
        raise HTTPException(status_code=400, detail="Item has no remaining uses")

    # Update the usage limit
    new_usage_limit = item["usageLimit"] - 1
    update_item(request.itemId, {"usageLimit": new_usage_limit})

    # Log the retrieval action
    log_details = {
        "action": "retrieval",
        "userId": request.userId,
        "timestamp": request.timestamp,
        "itemId": request.itemId
    }
    log_entry = Log(
        timestamp=request.timestamp,
        userId=request.userId,
        actionType="retrieval",
        itemId=request.itemId,
        details=json.dumps(log_details)
    )
    create_log(log_entry)

    return {"success": True}