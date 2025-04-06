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

    - **startDate**: Filter logs after this date (ISO format, e.g., "2023-10-25T12:00:00Z").
    - **endDate**: Filter logs before this date (ISO format).
    - **itemId**: Filter by item ID.
    - **userId**: Filter by user ID.
    - **actionType**: Filter by action type (e.g., "retrieval").
    - Returns: A dictionary with a list of logs, e.g., {"logs": [{...}, {...}]}.
    """
    logs = get_logs(startDate=startDate, endDate=endDate, itemId=itemId, userId=userId, actionType=actionType)
    return {"logs": logs}