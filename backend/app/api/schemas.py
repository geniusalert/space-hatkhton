from pydantic import BaseModel
from typing import Optional, List

class RetrieveRequest(BaseModel):
    itemId: str
    userId: str
    timestamp: str  # Expected in ISO format, e.g., "2023-10-25T12:00:00Z"

class Log(BaseModel):
    timestamp: str
    userId: str
    actionType: str
    itemId: str
    details: str

class Item(BaseModel):
    itemId: str
    name: str
    width: float
    depth: float
    height: float
    weight: float
    usageLimit: int
    expiryDate: Optional[str] = None
    containerId: Optional[str] = None
    startW: Optional[float] = 0
    startD: Optional[float] = 0
    startH: Optional[float] = 0
    endW: Optional[float] = 0
    endD: Optional[float] = 0
    endH: Optional[float] = 0

class Container(BaseModel):
    containerId: str
    width: float
    depth: float
    height: float

class PlacementRequest(BaseModel):
    items: List[Item]
    containers: List[Container]

class PlacementResponse(BaseModel):
    success: bool
    placements: List[dict]