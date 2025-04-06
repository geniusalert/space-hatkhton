# backend/app/crud.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple

# Assuming models and schemas are defined in these files
# Adjust imports based on your actual project structure
from . import models, schemas

# --- Item Definition CRUD ---

def get_item_definition(db: Session, item_id: str) -> Optional[models.ItemDefinition]:
    """Gets the original definition/template of an item by its ID."""
    return db.query(models.ItemDefinition).filter(models.ItemDefinition.itemId == item_id).first()

def get_item_definition_by_name(db: Session, item_name: str) -> Optional[models.ItemDefinition]:
    """Gets the original definition/template of an item by its name."""
    return db.query(models.ItemDefinition).filter(models.ItemDefinition.name == item_name).first()

def get_all_item_definitions(db: Session, skip: int = 0, limit: int = 100) -> List[models.ItemDefinition]:
    """Gets all item definitions (templates)."""
    return db.query(models.ItemDefinition).offset(skip).limit(limit).all()

def create_item_definition(db: Session, item: schemas.ItemCreate) -> models.ItemDefinition:
    """Creates a new item definition (template)."""
    db_item = models.ItemDefinition(**item.model_dump())
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Item definition with ID '{item.itemId}' or Name '{item.name}' may already exist.")


# --- Container CRUD ---

def get_container_by_id(db: Session, container_id: str) -> Optional[models.Container]:
    """Gets a container by its ID."""
    return db.query(models.Container).filter(models.Container.containerId == container_id).first()

def get_all_containers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Container]:
    """Gets all containers."""
    return db.query(models.Container).offset(skip).limit(limit).all()

def create_container(db: Session, container: schemas.ContainerCreate) -> models.Container:
    """Creates a new container."""
    db_container = models.Container(**container.model_dump())
    db.add(db_container)
    try:
        db.commit()
        db.refresh(db_container)
        return db_container
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Container with ID '{container.containerId}' may already exist.")


# --- Placed Item CRUD ---

def add_placed_item(db: Session, item_placement: schemas.PlacedItemCreate) -> models.PlacedItem:
    """Adds a record of an item being placed in a container."""
    # Check if the item definition exists
    item_def = get_item_definition(db, item_placement.itemId)
    if not item_def:
        raise ValueError(f"Cannot place item: Item definition with ID '{item_placement.itemId}' not found.")

    # Check if container exists
    container = get_container_by_id(db, item_placement.containerId)
    if not container:
         raise ValueError(f"Cannot place item: Container with ID '{item_placement.containerId}' not found.")

    # Create the placed item record
    # Ensure PlacedItem model can be created from PlacedItemCreate schema + item_def details
    db_placed_item = models.PlacedItem(
        itemId=item_placement.itemId,
        name=item_def.name, # Get name from definition
        containerId=item_placement.containerId,
        startW=item_placement.startW,
        startD=item_placement.startD,
        startH=item_placement.startH,
        width=item_placement.width,
        depth=item_placement.depth,
        height=item_placement.height,
        priority=item_def.priority, # Get priority from definition
        # Add other relevant fields from item_def if needed in PlacedItem model
    )
    db.add(db_placed_item)
    try:
        db.commit()
        db.refresh(db_placed_item)
        return db_placed_item
    except IntegrityError: # e.g., if you have a unique constraint on (itemId, containerId)
        db.rollback()
        raise ValueError(f"Item '{item_placement.itemId}' might already be placed at this exact location or have constraint conflict.")

def get_placed_item_by_id(db: Session, item_id: str, container_id: Optional[str] = None) -> Optional[models.PlacedItem]:
    """
    Gets a specific placed item instance by its unique item ID.
    Optionally filter by container ID if multiple placements of the same item ID are possible (unlikely based on schema).
    """
    query = db.query(models.PlacedItem).filter(models.PlacedItem.itemId == item_id)
    if container_id:
         query = query.filter(models.PlacedItem.containerId == container_id)
    return query.first() # Assumes itemId is unique across all placements

def get_placed_items_by_name(db: Session, item_name: str) -> List[models.PlacedItem]:
    """Gets all placed item instances matching a given name."""
    # Assumes PlacedItem model has a 'name' field populated from ItemDefinition
    return db.query(models.PlacedItem).filter(models.PlacedItem.name == item_name).all()

def get_items_in_container(db: Session, container_id: str) -> List[models.PlacedItem]:
    """Gets all items currently placed within a specific container."""
    return db.query(models.PlacedItem).filter(models.PlacedItem.containerId == container_id).all()

def get_all_placed_items(db: Session) -> List[models.PlacedItem]:
    """Gets all items currently placed in any container."""
    return db.query(models.PlacedItem).all()

def remove_placed_item(db: Session, item_id: str, container_id: str) -> bool:
    """Removes a placed item record from a container."""
    db_item = get_placed_item_by_id(db, item_id=item_id, container_id=container_id)
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False # Item not found in that container

def update_placed_item_position(
    db: Session,
    item_id: str,
    container_id: str,
    new_pos: Tuple[float, float, float],
    new_dims: Optional[Tuple[float, float, float]] = None # If rotation changes dims
) -> Optional[models.PlacedItem]:
    """Updates the position (and optionally dimensions) of a placed item."""
    db_item = get_placed_item_by_id(db, item_id=item_id, container_id=container_id)
    if db_item:
        db_item.startW, db_item.startD, db_item.startH = new_pos
        if new_dims:
            db_item.width, db_item.depth, db_item.height = new_dims
        db.commit()
        db.refresh(db_item)
        return db_item
    return None # Item not found

# --- Log CRUD ---

def create_log(db: Session, log: schemas.LogCreate) -> models.Log:
    """Creates a log entry."""
    # Example assumes Log model takes userId, action, details, timestamp
    # Adjust field names as per your models.Log definition
    db_log = models.Log(
        userId=log.userId,
        action=log.action,
        details=log.details
        # timestamp might be handled automatically by the database model default
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_logs(db: Session, skip: int = 0, limit: int = 100) -> List[models.Log]:
    """Retrieves log entries, ordered by timestamp descending."""
    # Assumes Log model has a 'timestamp' field
    return db.query(models.Log).order_by(models.Log.timestamp.desc()).offset(skip).limit(limit).all()