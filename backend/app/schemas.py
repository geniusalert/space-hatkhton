# backend/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date

# --- Configuration for ORM Mode ---
# Used in schemas that read data directly from SQLAlchemy models
orm_config = {"from_attributes": True}


# --- Item Definition Schemas ---

class ItemBase(BaseModel):
    """Base schema for item properties."""
    name: str
    width: float = Field(..., gt=0, description="Width of the item (along X-axis)")
    depth: float = Field(..., gt=0, description="Depth of the item (along Y-axis)")
    height: float = Field(..., gt=0, description="Height of the item (along Z-axis)")
    mass: float = Field(..., gt=0, description="Mass of the item")
    priority: int = Field(..., ge=1, le=10, description="Priority (1-10, lower number means higher priority)")
    expiryDate: Optional[date] = Field(None, description="Expiry date (YYYY-MM-DD)")
    usageLimit: Optional[int] = Field(None, gt=0, description="Usage limit (e.g., number of times it can be retrieved)")
    preferredZone: Optional[str] = Field(None, description="Preferred storage zone")


class ItemCreate(ItemBase):
    """Schema for creating a new item definition (template)."""
    itemId: str = Field(..., description="Unique ID for this item type")


class Item(ItemBase):
    """Schema for reading an item definition (represents the DB model)."""
    itemId: str = Field(..., description="Unique ID for this item type")

    class Config(BaseModel.Config):
        # Allow creating this schema from a DB model object
        from_attributes = True


# --- Container Schemas ---

class ContainerBase(BaseModel):
    """Base schema for container properties."""
    zone: str = Field(..., description="Storage zone the container belongs to")
    width: float = Field(..., gt=0, description="Internal width of the container (X-axis)")
    depth: float = Field(..., gt=0, description="Internal depth of the container (Y-axis)")
    height: float = Field(..., gt=0, description="Internal height of the container (Z-axis)")


class ContainerCreate(ContainerBase):
    """Schema for creating a new container."""
    containerId: str = Field(..., description="Unique ID for the container")


class Container(ContainerBase):
    """Schema for reading a container (represents the DB model)."""
    containerId: str = Field(..., description="Unique ID for the container")

    class Config(BaseModel.Config):
        from_attributes = True


# --- Placed Item Schemas ---

class PlacedItemBase(BaseModel):
    """Base schema for placement details."""
    startW: float = Field(..., ge=0, description="Starting coordinate along the container's width (X-axis)")
    startD: float = Field(..., ge=0, description="Starting coordinate along the container's depth (Y-axis, front is 0)")
    startH: float = Field(..., ge=0, description="Starting coordinate along the container's height (Z-axis, bottom is 0)")
    # Dimensions of the item *as placed* (accounts for rotation)
    width: float = Field(..., gt=0, description="Width of the item as placed")
    depth: float = Field(..., gt=0, description="Depth of the item as placed")
    height: float = Field(..., gt=0, description="Height of the item as placed")


class PlacedItemCreate(PlacedItemBase):
    """Schema used as input when placing an item in a container."""
    itemId: str = Field(..., description="ID of the item definition being placed")
    containerId: str = Field(..., description="ID of the container where the item is placed")


class PlacedItem(PlacedItemBase):
    """Schema for reading a placed item (represents the DB model)."""
    itemId: str
    name: str # Populated from ItemDefinition in CRUD
    containerId: str
    priority: int # Populated from ItemDefinition in CRUD

    class Config(BaseModel.Config):
        from_attributes = True


# --- Placement API Schemas ---

class PlacementRequest(BaseModel):
    """Request body for the placement API endpoint."""
    itemId: str = Field(..., description="ID of the item definition to place")
    userId: str = Field(..., description="ID of the user performing the action")


class PlacementResponse(BaseModel):
    """Response body for a successful placement."""
    message: str = "Placement successful"
    placed_item: PlacedItem


# --- Search/Retrieval Schemas ---

class RetrievalInstruction(BaseModel):
    """Instruction step for retrieving an item."""
    move: str = Field(..., description="Item ID to move")
    from_container: str = Field(..., alias="from", description="Container ID the item is currently in")


class SearchResultItem(BaseModel):
    """Represents a single item found during search, including retrieval info."""
    item: PlacedItem = Field(..., description="Details of the placed item found")
    retrieval_steps: int = Field(..., description="Number of other items that need to be moved to retrieve this item")
    blocking_items: List[str] = Field(..., description="List of item IDs that are directly blocking retrieval")
    retrieval_instructions: List[RetrievalInstruction] = Field(..., description="Step-by-step moves required")
    score: Optional[float] = Field(None, description="Calculated score for retrieval priority (lower is better)")


class SearchResponse(BaseModel):
    """Overall response for the search API."""
    results: List[SearchResultItem]


# --- Log Schemas ---

class LogBase(BaseModel):
    """Base schema for log entries."""
    userId: str = Field(..., description="ID of the user performing the action")
    action: str = Field(..., description="Description of the action performed")
    details: Optional[str] = Field(None, description="Additional details about the action")


class LogCreate(LogBase):
    """Schema for creating a new log entry."""
    pass


class Log(LogBase):
    """Schema for reading a log entry (represents the DB model)."""
    id: int = Field(..., description="Unique ID of the log entry")
    timestamp: datetime = Field(..., description="Timestamp when the action occurred")

    class Config(BaseModel.Config):
        from_attributes = True


# --- Waste Management Schemas ---

class WasteItem(PlacedItem):
    """Represents an item identified as waste."""
    # Potentially add reasons or expiry date info if needed
    days_to_expiry: Optional[float] = None # Example additional field


class WastePlanRequest(BaseModel):
    """Input for planning waste removal."""
    undocking_container_id: str = Field(..., description="Target container ID for waste items")
    max_weight: float = Field(..., gt=0, description="Maximum total weight allowed in the undocking container")
    userId: str = Field(..., description="ID of the user performing the action")


class WastePlanResponseItem(BaseModel):
    """Item included in the waste removal plan."""
    itemId: str
    name: str
    from_containerId: str
    mass: float


class WastePlanResponse(BaseModel):
    """Output of the waste removal plan."""
    items_to_move: List[WastePlanResponseItem]
    total_items: int
    total_weight: float


# --- Import/Export Schemas ---

class BulkImportRequest(BaseModel):
    """Request for bulk importing items and containers."""
    items: List[ItemCreate] = Field(default_factory=list)
    containers: List[ContainerCreate] = Field(default_factory=list)
    userId: str = Field(..., description="ID of the user performing the import")


class BulkImportResponse(BaseModel):
    """Response after bulk import."""
    items_created: int
    containers_created: int
    errors: List[str] = Field(default_factory=list)


class ExportDataResponse(BaseModel):
    """Response containing exported data."""
    items: List[Item]
    containers: List[Container]
    placed_items: List[PlacedItem]


# --- Simulation Schemas ---
# These are basic examples, adjust based on your simulation logic

class SimulationEvent(BaseModel):
    """Represents an event that occurred during simulation."""
    timestamp: float # Simulation time
    event_type: str # e.g., "ITEM_EXPIRED", "USAGE_LIMIT_REACHED"
    details: Dict[str, Any]


class SimulationRequest(BaseModel):
    """Input parameters for running a time simulation."""
    duration_days: float = Field(..., gt=0, description="Number of days to simulate")
    # Add other parameters like event frequency, specific scenarios etc.
    userId: str = Field(..., description="ID of the user initiating the simulation")


class SimulationResult(BaseModel):
    """Output of the time simulation."""
    final_sim_time_days: float
    events_occurred: List[SimulationEvent]
    # Include final state summaries if needed (e.g., number of expired items)


# --- Generic Response Schema ---

class MessageResponse(BaseModel):
    """A generic response model for simple status messages."""
    message: str