from pydantic import BaseModel
from typing import Optional, List

# Coordinates for item positioning within containers
class Coordinates(BaseModel):
    width: float
    depth: float
    height: float

# Position of an item within a container
class Position(BaseModel):
    startCoordinates: Coordinates
    endCoordinates: Coordinates

# Item model for cargo
class Item(BaseModel):
    itemId: str
    name: str
    width: float
    depth: float
    height: float
    mass: float
    priority: int  # 1-100, higher is more critical
    expiryDate: Optional[str] = None  # ISO format (e.g., "2025-05-20")
    usageLimit: int  # Number of uses before becoming waste
    preferredZone: str  # Preferred storage zone
    containerId: Optional[str] = None  # Assigned container
    startW: Optional[float] = None  # Start width coordinate
    startD: Optional[float] = None  # Start depth coordinate
    startH: Optional[float] = None  # Start height coordinate
    endW: Optional[float] = None    # End width coordinate
    endD: Optional[float] = None    # End depth coordinate
    endH: Optional[float] = None    # End height coordinate

    class Config:
        orm_mode = True  # Allows conversion from SQLite rows to Pydantic models

# Container model for storage units
class Container(BaseModel):
    containerId: str
    zone: str  # e.g., "Crew Quarters", "Airlock"
    width: float
    depth: float
    height: float

    class Config:
        orm_mode = True

# Log model for tracking actions
class Log(BaseModel):
    timestamp: str  # ISO format (e.g., "2025-04-06T12:00:00Z")
    userId: str
    actionType: str  # e.g., "placement", "retrieval"
    itemId: str
    details: str  # JSON string with additional info

    class Config:
        orm_mode = True

# Request and Response Models for Placement API
class PlacementRequest(BaseModel):
    items: List[Item]
    containers: List[Container]

class PlacementResponse(BaseModel):
    success: bool
    placements: List[dict]  # Contains itemId, containerId, position

# Request and Response Models for Search/Retrieve API (simplified)
class RetrievalRequest(BaseModel):
    itemId: str
    userId: str
    timestamp: str

class RetrievalResponse(BaseModel):
    success: bool
    item: Optional[dict] = None
    retrievalSteps: List[dict] = []  # Steps to retrieve item