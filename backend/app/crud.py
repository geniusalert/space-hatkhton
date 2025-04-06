# backend/app/crud.py
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

# Assuming models and schemas are defined
from . import models, schemas # Adjust imports as per your project structure

logger = logging.getLogger(__name__)

# --- Item Definition CRUD ---

def get_item_definition(db: Session, item_definition_id: int) -> Optional[models.ItemDefinition]:
    # *** Optimization: Add DB index on models.ItemDefinition.id ***
    return db.query(models.ItemDefinition).filter(models.ItemDefinition.id == item_definition_id).first()

def get_item_definitions(db: Session, skip: int = 0, limit: int = 100) -> List[models.ItemDefinition]:
    return db.query(models.ItemDefinition).offset(skip).limit(limit).all()

def create_item_definition(db: Session, item_def: schemas.ItemDefinitionCreate) -> models.ItemDefinition:
    db_item_def = models.ItemDefinition(**item_def.model_dump())
    db.add(db_item_def)
    db.commit()
    db.refresh(db_item_def)
    logger.info(f"Created item definition: {db_item_def.name} (ID: {db_item_def.id})")
    return db_item_def

# --- Container CRUD ---

def get_container(db: Session, container_id: int) -> Optional[models.Container]:
     # *** Optimization: Add DB index on models.Container.id ***
    return db.query(models.Container).filter(models.Container.id == container_id).first()

def get_containers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Container]:
    # *** Optimization: Add DB index on models.Container.zone if filtering by zone often ***
    return db.query(models.Container).offset(skip).limit(limit).all()

def create_container(db: Session, container: schemas.ContainerCreate) -> models.Container:
    db_container = models.Container(**container.model_dump())
    db.add(db_container)
    db.commit()
    db.refresh(db_container)
    logger.info(f"Created container: {db_container.name} (ID: {db_container.id})")
    return db_container

# --- Placed Item CRUD ---

def get_placed_item(db: Session, placed_item_id: int) -> Optional[models.PlacedItem]:
    # *** Optimization: Add DB index on models.PlacedItem.id ***
    return db.query(models.PlacedItem).filter(models.PlacedItem.id == placed_item_id).first()

def get_placed_items_by_container(db: Session, container_id: int) -> List[models.PlacedItem]:
    # *** Optimization: Add DB index on models.PlacedItem.container_id ***
    return db.query(models.PlacedItem).filter(models.PlacedItem.container_id == container_id).all()

def get_all_placed_items(db: Session) -> List[models.PlacedItem]:
    """Gets all placed items. Can be memory intensive for very large datasets."""
    logger.warning("Fetching ALL placed items. Consider pagination or filtering for large datasets.")
    return db.query(models.PlacedItem).all()

def create_placed_item(db: Session, item: schemas.PlacedItemCreate, placement_details: Dict[str, Any]) -> models.PlacedItem:
    """Creates a PlacedItem entry using details from the placement algorithm."""
    # Merge item data with placement details
    item_data = item.model_dump()
    item_data.update({
        "container_id": placement_details["container_id"],
        "pos_x": placement_details["pos_x"],
        "pos_y": placement_details["pos_y"],
        "pos_z": placement_details["pos_z"],
        "width": placement_details["placed_width"], # Store actual placed dimensions
        "height": placement_details["placed_height"],
        "depth": placement_details["placed_depth"],
        "placement_timestamp": datetime.now(timezone.utc),
        "currentUsage": 0 # Initialize usage count
    })
    db_item = models.PlacedItem(**item_data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logger.info(f"Placed item definition {item.item_definition_id} as PlacedItem ID {db_item.id} in container {db_item.container_id}")
    # Log this action (consider moving logging logic here or calling a logging service)
    # log_action(db, action_type="placement", item_id=db_item.id, details=f"Placed in C{db_item.container_id}")
    return db_item

def update_item_placement(db: Session, placed_item_id: int, move_details: Dict[str, Any]) -> Optional[models.PlacedItem]:
    """Updates the position and container of an existing placed item."""
    db_item = get_placed_item(db, placed_item_id)
    if not db_item:
        logger.error(f"Cannot update placement: PlacedItem ID {placed_item_id} not found.")
        return None

    # *** Use DB Transaction ***
    try:
        original_container = db_item.container_id
        db_item.container_id = move_details["container_id"]
        db_item.pos_x = move_details["pos_x"]
        db_item.pos_y = move_details["pos_y"]
        db_item.pos_z = move_details["pos_z"]
        # Update width/height/depth if rotation changed (assuming move_details includes these)
        if "placed_width" in move_details: db_item.width = move_details["placed_width"]
        if "placed_height" in move_details: db_item.height = move_details["placed_height"]
        if "placed_depth" in move_details: db_item.depth = move_details["placed_depth"]

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        logger.info(f"Updated placement for PlacedItem ID {placed_item_id}. Moved to C{db_item.container_id} at ({db_item.pos_x}, {db_item.pos_y}, {db_item.pos_z})")
        # Log this action
        # log_action(db, action_type="move", item_id=db_item.id, details=f"Moved from C{original_container} to C{db_item.container_id}")
        return db_item
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error updating placement for item {placed_item_id}: {e}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating placement for item {placed_item_id}: {e}")
        return None


def increment_item_usage(db: Session, placed_item_id: int) -> Optional[models.PlacedItem]:
     """Increments the usage count for an item."""
     # *** Use DB Transaction ***
     db_item = get_placed_item(db, placed_item_id)
     if not db_item:
         logger.error(f"Cannot increment usage: PlacedItem ID {placed_item_id} not found.")
         return None

     try:
         if db_item.currentUsage is None:
             db_item.currentUsage = 0
         db_item.currentUsage += 1
         db.add(db_item)
         db.commit()
         db.refresh(db_item)
         logger.info(f"Incremented usage for PlacedItem ID {placed_item_id} to {db_item.currentUsage}")
         # Log this action
         # log_action(db, action_type="usage_increment", item_id=db_item.id, details=f"Usage incremented to {db_item.currentUsage}")
         return db_item
     except Exception as e:
         db.rollback()
         logger.error(f"Error incrementing usage for item {placed_item_id}: {e}")
         return None


def remove_placed_item(db: Session, placed_item_id: int) -> bool:
    """Removes a placed item from the database (e.g., after retrieval or disposal)."""
     # *** Use DB Transaction ***
    db_item = get_placed_item(db, placed_item_id)
    if db_item:
        try:
            item_def_id = db_item.item_definition_id
            container_id = db_item.container_id
            db.delete(db_item)
            db.commit()
            logger.info(f"Removed PlacedItem ID {placed_item_id} (Def ID: {item_def_id}) from container {container_id}")
             # Log this action
             # log_action(db, action_type="removal", item_id=placed_item_id, details=f"Item removed from system.")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error removing PlacedItem ID {placed_item_id}: {e}")
            return False
    else:
        logger.warning(f"Attempted to remove non-existent PlacedItem ID {placed_item_id}")
        return False

# --- Log CRUD ---

def create_log_entry(db: Session, log_entry: schemas.LogEntryCreate) -> models.LogEntry:
    db_log = models.LogEntry(
        timestamp=datetime.now(timezone.utc), # Ensure timestamp is set on creation
        action_type=log_entry.action_type,
        item_id=log_entry.item_id,
        container_id=log_entry.container_id,
        details=log_entry.details
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    # Avoid logging the log creation itself to prevent infinite loops if logging is broad
    # logger.debug(f"Created log entry: {db_log.id} - {db_log.action_type}")
    return db_log

def get_log_entries(db: Session, skip: int = 0, limit: int = 100) -> List[models.LogEntry]:
    # *** Optimization: Add DB index on models.LogEntry.timestamp (and potentially action_type/item_id if filtering) ***
    return db.query(models.LogEntry).order_by(models.LogEntry.timestamp.desc()).offset(skip).limit(limit).all()