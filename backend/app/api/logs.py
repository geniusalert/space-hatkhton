from fastapi import APIRouter, Query
from typing import Optional, List, Dict
from ..crud import get_logs

router = APIRouter()

@router.get("/api/logs")
async def get_action_logs(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    itemId: Optional[str] = Query(None),
    userId: Optional[str] = Query(None),
    actionType: Optional[str] = Query(None)
) -> Dict:
    """
    Retrieve logs filtered by date range, itemId, userId, or actionType.
    """
    logs = get_logs(item_id=itemId, user_id=userId)  # Simplified; extend for all filters
    filtered_logs = logs

    if startDate:
        filtered_logs = [log for log in filtered_logs if log["timestamp"] >= startDate]
    if endDate:
        filtered_logs = [log for log in filtered_logs if log["timestamp"] <= endDate]
    if actionType:
        filtered_logs = [log for log in filtered_logs if log["actionType"] == actionType]

    return {"logs": filtered_logs}