from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from ..crud import get_item, get_container, get_container_items
from ..utils.retrieval_algorithm import calculate_retrieval_steps
import logging

router = APIRouter()
logging.basicConfig(level=logging.INFO)

@router.get("/api/search")
async def search_item(
    itemId: Optional[str] = Query(None, description="Unique ID of the item"),
    itemName: Optional[str] = Query(None, description="Name of the item"),
    userId: Optional[str] = Query(None, description="ID of the user making the request")
):
    if not itemId and not itemName:
        raise HTTPException(status_code=400, detail="Either itemId or itemName must be provided")

    items: List[Dict] = []
    if itemId:
        item = get_item(itemId)
        if item:
            items = [item]
    # Note: get_items_by_name is not implemented here; for simplicity, we assume itemId for now

    if not items:
        return {"success": True, "found": False}

    item = items[0]
    container = get_container(item["containerId"])
    if container:
        zone = container["zone"]
    else:
        logging.warning(f"Container {item['containerId']} not found for item {item['itemId']}")
        zone = "Unknown"

    container_items: List[Dict] = get_container_items(item["containerId"])
    steps: List[Dict] = calculate_retrieval_steps(item, container_items)

    response_item = {
        "itemId": item["itemId"],
        "name": item["name"],
        "containerId": item["containerId"],
        "zone": zone,
        "position": {
            "startCoordinates": {"width": item["startW"], "depth": item["startD"], "height": item["startH"]},
            "endCoordinates": {"width": item["endW"], "depth": item["endD"], "height": item["endH"]}
        },
        "retrievalSteps": steps
    }

    return {"success": True, "found": True, "item": response_item}