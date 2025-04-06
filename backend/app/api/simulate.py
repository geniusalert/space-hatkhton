from fastapi import APIRouter
from datetime import datetime, timedelta
from typing import List, Dict
from ..crud import get_all_items, update_item

router = APIRouter()

@router.post("/api/simulate/day")
async def simulate_time(numOfDays: int) -> Dict:
    """
    Simulate time progression by a specified number of days.
    """
    items = get_all_items()
    current_date = datetime.now()
    new_date = current_date + timedelta(days=numOfDays)
    changes = {"itemsUsed": [], "itemsDepletedToday": []}

    for item in items:
        if item["usageLimit"] > 0:  # Simulate usage (simplified)
            new_usage = max(0, item["usageLimit"] - 1)
            update_item(item["itemId"], {"usageLimit": new_usage})
            changes["itemsUsed"].append({"itemId": item["itemId"], "name": item["name"]})
            if new_usage == 0:
                changes["itemsDepletedToday"].append({"itemId": item["itemId"], "name": item["name"]})

    return {
        "success": True,
        "newDate": new_date.isoformat(),
        "changes": changes
    }