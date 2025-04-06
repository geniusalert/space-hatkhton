from fastapi import APIRouter, HTTPException
from ..schemas import PlacementRequest, PlacementResponse
from ..utils.placement_algorithm import place_items
from ..crud import create_item, create_container

router = APIRouter()

@router.post("/api/placement", response_model=PlacementResponse)
async def placement(request: PlacementRequest):
    """
    API endpoint to place items into containers.

    - Uses a 3D bin-packing algorithm from placement_algorithm.py.
    - Stores item coordinates in the database.
    - Returns: Success status and placement details.
    """
    try:
        # Insert containers into the database
        for container in request.containers:
            create_container(container)
        
        # Place items using the algorithm
        placements = place_items(request.items, request.containers)
        
        # Store placed items in the database with coordinates
        for placement in placements:
            item = next(i for i in request.items if i.itemId == placement["itemId"])
            item.containerId = placement["containerId"]
            item.startW, item.startD, item.startH = placement["position"]["startCoordinates"]
            item.endW, item.endD, item.endH = placement["position"]["endCoordinates"]
            create_item(item)
        
        return {"success": True, "placements": placements}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))