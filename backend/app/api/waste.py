from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Dict
from ..crud import get_all_items, get_container, update_item

router = APIRouter()

@router.get("/api/waste/identify")
async def identify_waste() -> Dict:
    """
    Identify items that are expired or out of uses.
    """
    items = get_all_items()
    waste_items = []
    current_date = datetime.now().isoformat()

    for item in items:
        is_expired = item["expiryDate"] and item["expiryDate"] < current_date
        is_depleted = item["usageLimit"] <= 0
        if is_expired or is_depleted:
            waste_items.append({
                "itemId": item["itemId"],
                "name": item["name"],
                "reason": "Expired" if is_expired else "Out of Uses",
                "containerId": item["containerId"],
                "position": {
                    "startCoordinates": {"width": item["startW"], "depth": item["startD"], "height": item["startH"]},
                    "endCoordinates": {"width": item["endW"], "depth": item["endD"], "height": item["endH"]}
                }
            })

    return {"success": True, "wasteItems": waste_items}

@router.post("/api/waste/return-plan")
async def waste_return_plan(undockingContainerId: str, undockingDate: str, maxWeight: float) -> Dict:
    """
    Plan to move waste items to an undocking module.
    """
    waste_items = (await identify_waste())["wasteItems"]
    container = get_container(undockingContainerId)
    if not container:
        raise HTTPException(status_code=404, detail="Undocking container not found")

    total_weight = 0
    total_volume = 0
    return_items = []

    for item in waste_items:
        item_weight = get_item_weight(item["itemId"])  # Assume this function exists in crud.py
        item_volume = (item["position"]["endCoordinates"]["width"] - item["position"]["startCoordinates"]["width"]) * \
                      (item["position"]["endCoordinates"]["depth"] - item["position"]["startCoordinates"]["depth"]) * \
                      (item["position"]["endCoordinates"]["height"] - item["position"]["startCoordinates"]["height"])
        if total_weight + item_weight <= maxWeight:
            total_weight += item_weight
            total_volume += item_volume
            return_items.append({
                "itemId": item["itemId"],
                "name": item["name"],
                "reason": item["reason"]
            })
            update_item(item["itemId"], {"containerId": undockingContainerId})

    return {
        "success": True,
        "returnManifest": {
            "undockingContainerId": undockingContainerId,
            "undockingDate": undockingDate,
            "returnItems": return_items,
            "totalVolume": total_volume,
            "totalWeight": total_weight
        }
    }