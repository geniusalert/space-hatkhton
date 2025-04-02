/**
 * Basic Operations for Space Cargo Management System
 * 
 * This module extends the spatial grid implementation with:
 * - Item rotation (6 possible orientations)
 * - Collision detection between items
 * - Visibility checking from container's open face
 * - Item accessibility scoring
 */

const { Position, Dimensions, SpatialGrid } = require('./spatial-grid-implementation');

/**
 * Orientation represents one of the 6 possible ways an item can be rotated
 * The orientation is defined by which dimensions go along which axes:
 * - [0,1,2]: Original orientation (width along x, depth along y, height along z)
 * - [0,2,1]: Depth and height swapped (width along x, height along y, depth along z)
 * - [1,0,2]: Width and depth swapped (depth along x, width along y, height along z)
 * - [1,2,0]: Width along y, height along x, depth along z
 * - [2,0,1]: Width along z, depth along x, height along y
 * - [2,1,0]: Width along z, height along x, depth along y
 */
class Orientation {
  constructor(widthAxis, depthAxis, heightAxis) {
    // Validate that this is a valid permutation of [0,1,2]
    const axes = [widthAxis, depthAxis, heightAxis].sort();
    if (axes[0] !== 0 || axes[1] !== 1 || axes[2] !== 2) {
      throw new Error("Invalid orientation: must be a permutation of [0,1,2]");
    }
    
    this.widthAxis = widthAxis;   // Which axis the width dimension goes along (0=x, 1=y, 2=z)
    this.depthAxis = depthAxis;   // Which axis the depth dimension goes along (0=x, 1=y, 2=z)
    this.heightAxis = heightAxis; // Which axis the height dimension goes along (0=x, 1=y, 2=z)
  }
  
  // Get the effective dimensions when item is oriented in this way
  getEffectiveDimensions(originalDimensions) {
    const dims = [originalDimensions.width, originalDimensions.depth, originalDimensions.height];
    return new Dimensions(
      dims[this.widthAxis],
      dims[this.depthAxis],
      dims[this.heightAxis]
    );
  }
  
  static getAllOrientations() {
    return [
      new Orientation(0, 1, 2), // Original orientation
      new Orientation(0, 2, 1), // Rotate around x-axis
      new Orientation(1, 0, 2), // Rotate around z-axis
      new Orientation(1, 2, 0), // Rotate around y-axis then x-axis
      new Orientation(2, 0, 1), // Rotate around y-axis
      new Orientation(2, 1, 0)  // Rotate around x-axis then z-axis
    ];
  }
  
  toString() {
    return `Orientation(w:${this.widthAxis}, d:${this.depthAxis}, h:${this.heightAxis})`;
  }
}

/**
 * Extended SpatialGrid class with additional operations for cargo management
 */
class EnhancedSpatialGrid extends SpatialGrid {
  constructor(containerDimensions, openFace = "front") {
    super(containerDimensions);
    
    // Define which face of the container is open (front, back, top, bottom, left, right)
    // This affects visibility and accessibility calculations
    this.openFace = openFace;
    
    // Store items with their full information (not just their IDs)
    this.itemsData = new Map(); // Maps itemId to full item data
  }
  
  /**
   * Try to place an item with all possible orientations
   * Returns array of valid positions and orientations
   */
  findValidPlacements(itemDimensions, itemId) {
    const validPlacements = [];
    const orientations = Orientation.getAllOrientations();
    
    for (const orientation of orientations) {
      const effectiveDimensions = orientation.getEffectiveDimensions(itemDimensions);
      
      // Find empty spaces that can fit these dimensions
      const emptySpaces = this.findEmptySpaces(effectiveDimensions);
      
      // For each empty space, create a valid placement
      for (const position of emptySpaces) {
        validPlacements.push({
          position,
          orientation,
          effectiveDimensions
        });
      }
    }
    
    return validPlacements;
  }
  
  /**
   * Place item with a specific orientation
   */
  placeItem(itemData, position, orientation) {
    const effectiveDimensions = orientation.getEffectiveDimensions(itemData.dimensions);
    
    // Check if space is free
    if (!this.isSpaceFree(position, effectiveDimensions)) {
      return false;
    }
    
    // Occupy the space
    this.occupySpace(position, effectiveDimensions, itemData.id);
    
    // Store the item data with its position and orientation
    this.itemsData.set(itemData.id, {
      ...itemData,
      position,
      orientation,
      effectiveDimensions
    });
    
    return true;
  }
  
  /**
   * Check if two items collide
   */
  doItemsCollide(itemId1, itemId2) {
    if (!this.itemsData.has(itemId1) || !this.itemsData.has(itemId2)) {
      throw new Error("One or both items not found");
    }
    
    const item1 = this.itemsData.get(itemId1);
    const item2 = this.itemsData.get(itemId2);
    
    // Get bounding boxes
    const box1 = {
      minX: item1.position.x,
      minY: item1.position.y,
      minZ: item1.position.z,
      maxX: item1.position.x + item1.effectiveDimensions.width - 1,
      maxY: item1.position.y + item1.effectiveDimensions.depth - 1,
      maxZ: item1.position.z + item1.effectiveDimensions.height - 1
    };
    
    const box2 = {
      minX: item2.position.x,
      minY: item2.position.y,
      minZ: item2.position.z,
      maxX: item2.position.x + item2.effectiveDimensions.width - 1,
      maxY: item2.position.y + item2.effectiveDimensions.depth - 1,
      maxZ: item2.position.z + item2.effectiveDimensions.height - 1
    };
    
    // Check for overlap in all three dimensions
    return (
      box1.minX <= box2.maxX && box1.maxX >= box2.minX &&
      box1.minY <= box2.maxY && box1.maxY >= box2.minY &&
      box1.minZ <= box2.maxZ && box1.maxZ >= box2.minZ
    );
  }
  
  /**
   * Check if an item is directly visible from the container's open face
   */
  isItemVisible(itemId) {
    if (!this.itemsData.has(itemId)) {
      throw new Error(`Item with ID ${itemId} not found`);
    }
    
    const item = this.itemsData.get(itemId);
    const itemPosition = item.position;
    const itemDims = item.effectiveDimensions;
    
    // Define visibility check based on which face is open
    switch (this.openFace) {
      case "front": // Open at y=0
        // Check if any part of the item is at y=0
        return itemPosition.y === 0;
        
      case "back": // Open at y=max
        // Check if any part of the item touches the back face
        return itemPosition.y + itemDims.depth - 1 === this.dimensions.depth - 1;
        
      case "left": // Open at x=0
        // Check if any part of the item is at x=0
        return itemPosition.x === 0;
        
      case "right": // Open at x=max
        // Check if any part of the item touches the right face
        return itemPosition.x + itemDims.width - 1 === this.dimensions.width - 1;
        
      case "top": // Open at z=max
        // Check if any part of the item touches the top face
        return itemPosition.z + itemDims.height - 1 === this.dimensions.height - 1;
        
      case "bottom": // Open at z=0
        // Check if any part of the item is at z=0
        return itemPosition.z === 0;
        
      default:
        throw new Error(`Invalid open face: ${this.openFace}`);
    }
  }
  
  /**
   * Calculate visibility score for an item (percentage of the item visible from open face)
   */
  calculateVisibilityScore(itemId) {
    if (!this.itemsData.has(itemId)) {
      throw new Error(`Item with ID ${itemId} not found`);
    }
    
    const item = this.itemsData.get(itemId);
    const itemPos = item.position;
    const itemDims = item.effectiveDimensions;
    
    // Total cells occupied by the item
    const totalCells = itemDims.width * itemDims.depth * itemDims.height;
    let visibleCells = 0;
    
    // Function to check if a specific cell is visible
    const isCellVisible = (x, y, z) => {
      switch (this.openFace) {
        case "front": // Open at y=0
          // Check if there's a clear path from this cell to the front
          for (let checkY = 0; checkY < y; checkY++) {
            if (this.isPositionOccupied(new Position(x, checkY, z)) && 
                this.grid[x][checkY][z] !== itemId) {
              return false;
            }
          }
          return true;
          
        case "back": // Open at y=max
          // Check if there's a clear path from this cell to the back
          for (let checkY = y + 1; checkY < this.dimensions.depth; checkY++) {
            if (this.isPositionOccupied(new Position(x, checkY, z)) && 
                this.grid[x][checkY][z] !== itemId) {
              return false;
            }
          }
          return true;
          
        case "left": // Open at x=0
          // Check if there's a clear path from this cell to the left
          for (let checkX = 0; checkX < x; checkX++) {
            if (this.isPositionOccupied(new Position(checkX, y, z)) && 
                this.grid[checkX][y][z] !== itemId) {
              return false;
            }
          }
          return true;
          
        case "right": // Open at x=max
          // Check if there's a clear path from this cell to the right
          for (let checkX = x + 1; checkX < this.dimensions.width; checkX++) {
            if (this.isPositionOccupied(new Position(checkX, y, z)) && 
                this.grid[checkX][y][z] !== itemId) {
              return false;
            }
          }
          return true;
          
        case "top": // Open at z=max
          // Check if there's a clear path from this cell to the top
          for (let checkZ = z + 1; checkZ < this.dimensions.height; checkZ++) {
            if (this.isPositionOccupied(new Position(x, y, checkZ)) && 
                this.grid[x][y][checkZ] !== itemId) {
              return false;
            }
          }
          return true;
          
        case "bottom": // Open at z=0
          // Check if there's a clear path from this cell to the bottom
          for (let checkZ = 0; checkZ < z; checkZ++) {
            if (this.isPositionOccupied(new Position(x, y, checkZ)) && 
                this.grid[x][y][checkZ] !== itemId) {
              return false;
            }
          }
          return true;
      }
    };
    
    // Count visible cells
    for (let dx = 0; dx < itemDims.width; dx++) {
      for (let dy = 0; dy < itemDims.depth; dy++) {
        for (let dz = 0; dz < itemDims.height; dz++) {
          const x = itemPos.x + dx;
          const y = itemPos.y + dy;
          const z = itemPos.z + dz;
          
          if (isCellVisible(x, y, z)) {
            visibleCells++;
          }
        }
      }
    }
    
    // Return the percentage of visible cells
    return (visibleCells / totalCells) * 100;
  }
  
  /**
   * Calculate accessibility score for an item
   * This is based on:
   * 1. Visibility from the open face
   * 2. Number of items that must be moved to retrieve this item
   * 3. Distance from the open face
   */
  calculateAccessibilityScore(itemId) {
    if (!this.itemsData.has(itemId)) {
      throw new Error(`Item with ID ${itemId} not found`);
    }
    
    const item = this.itemsData.get(itemId);
    const itemPos = item.position;
    
    // 1. Visibility component (0-40 points)
    const visibilityScore = this.calculateVisibilityScore(itemId);
    const visibilityComponent = (visibilityScore / 100) * 40;
    
    // 2. Blocking items component (0-40 points)
    // Find all items that block this item
    const blockingItems = this.findBlockingItems(itemId);
    // More blocking items = lower score
    const blockingComponent = Math.max(0, 40 - (blockingItems.length * 10));
    
    // 3. Distance component (0-20 points)
    // Calculate distance from the open face
    let distance;
    switch (this.openFace) {
      case "front":
        distance = itemPos.y;
        break;
      case "back":
        distance = this.dimensions.depth - (itemPos.y + item.effectiveDimensions.depth);
        break;
      case "left":
        distance = itemPos.x;
        break;
      case "right":
        distance = this.dimensions.width - (itemPos.x + item.effectiveDimensions.width);
        break;
      case "top":
        distance = this.dimensions.height - (itemPos.z + item.effectiveDimensions.height);
        break;
      case "bottom":
        distance = itemPos.z;
        break;
    }
    
    // Normalize distance to a 0-20 scale
    // Maximum possible distance is the container dimension in that direction
    let maxDistance;
    switch (this.openFace) {
      case "front":
      case "back":
        maxDistance = this.dimensions.depth;
        break;
      case "left":
      case "right":
        maxDistance = this.dimensions.width;
        break;
      case "top":
      case "bottom":
        maxDistance = this.dimensions.height;
        break;
    }
    
    const distanceComponent = Math.max(0, 20 - ((distance / maxDistance) * 20));
    
    // Total accessibility score (0-100)
    return visibilityComponent + blockingComponent + distanceComponent;
  }
  
  /**
   * Find all items that block access to a given item
   */
  findBlockingItems(itemId) {
    if (!this.itemsData.has(itemId)) {
      throw new Error(`Item with ID ${itemId} not found`);
    }
    
    const item = this.itemsData.get(itemId);
    const itemPos = item.position;
    const itemDims = item.effectiveDimensions;
    
    const blockingItems = new Set();
    
    // Function to check cells between the item and the open face
    const checkCellsInPath = (startX, startY, startZ, endX, endY, endZ) => {
      for (let x = startX; x <= endX; x++) {
        for (let y = startY; y <= endY; y++) {
          for (let z = startZ; z <= endZ; z++) {
            const cellContent = this.grid[x][y][z];
            if (cellContent !== null && cellContent !== itemId) {
              blockingItems.add(cellContent);
            }
          }
        }
      }
    };
    
    // Check all cells between the item and the open face
    switch (this.openFace) {
      case "front": // Open at y=0
        checkCellsInPath(
          itemPos.x, 0, itemPos.z,
          itemPos.x + itemDims.width - 1, itemPos.y - 1, itemPos.z + itemDims.height - 1
        );
        break;
        
      case "back": // Open at y=max
        checkCellsInPath(
          itemPos.x, itemPos.y + itemDims.depth, itemPos.z,
          itemPos.x + itemDims.width - 1, this.dimensions.depth - 1, itemPos.z + itemDims.height - 1
        );
        break;
        
      case "left": // Open at x=0
        checkCellsInPath(
          0, itemPos.y, itemPos.z,
          itemPos.x - 1, itemPos.y + itemDims.depth - 1, itemPos.z + itemDims.height - 1
        );
        break;
        
      case "right": // Open at x=max
        checkCellsInPath(
          itemPos.x + itemDims.width, itemPos.y, itemPos.z,
          this.dimensions.width - 1, itemPos.y + itemDims.depth - 1, itemPos.z + itemDims.height - 1
        );
        break;
        
      case "top": // Open at z=max
        checkCellsInPath(
          itemPos.x, itemPos.y, itemPos.z + itemDims.height,
          itemPos.x + itemDims.width - 1, itemPos.y + itemDims.depth - 1, this.dimensions.height - 1
        );
        break;
        
      case "bottom": // Open at z=0
        checkCellsInPath(
          itemPos.x, itemPos.y, 0,
          itemPos.x + itemDims.width - 1, itemPos.y + itemDims.depth - 1, itemPos.z - 1
        );
        break;
    }
    
    return Array.from(blockingItems);
  }
  
  /**
   * Generate a retrieval plan - sequence of items to remove to access a target item
   */
  generateRetrievalPlan(targetItemId) {
    if (!this.itemsData.has(targetItemId)) {
      throw new Error(`Target item with ID ${targetItemId} not found`);
    }
    
    // If the item is directly visible/accessible, no need to move other items
    if (this.isItemVisible(targetItemId) && this.findBlockingItems(targetItemId).length === 0) {
      return {
        targetItem: targetItemId,
        itemsToMove: [],
        steps: [`Retrieve item ${targetItemId} directly`]
      };
    }
    
    // Get blocking items
    const blockingItems = this.findBlockingItems(targetItemId);
    
    // For each blocking item, we need to check what items block it
    const itemsToMove = [];
    const steps = [];
    
    // Simple implementation - just move blocking items in order
    // A more advanced implementation would use a graph to find the optimal sequence
    for (const blockingItemId of blockingItems) {
      itemsToMove.push(blockingItemId);
      steps.push(`Move item ${blockingItemId} to access ${targetItemId}`);
    }
    
    steps.push(`Retrieve item ${targetItemId}`);
    
    return {
      targetItem: targetItemId,
      itemsToMove,
      steps
    };
  }
}

// Example usage
function demonstrateBasicOperations() {
  // Create a container with dimensions 10x8x5
  const containerDims = new Dimensions(10, 8, 5);
  const container = new EnhancedSpatialGrid(containerDims, "front");
  
  // Create some items
  const item1 = {
    id: "ITEM001",
    name: "First Aid Kit",
    dimensions: new Dimensions(3, 2, 2),
    mass: 2.5,
    priority: "high"
  };
  
  const item2 = {
    id: "ITEM002",
    name: "Tool Box",
    dimensions: new Dimensions(2, 3, 1),
    mass: 4.0,
    priority: "medium"
  };
  
  // Place items with specific orientations
  const orientation1 = new Orientation(0, 1, 2); // Standard orientation
  container.placeItem(item1, new Position(0, 0, 0), orientation1);
  
  const orientation2 = new Orientation(1, 0, 2); // Rotated around z-axis
  container.placeItem(item2, new Position(4, 2, 0), orientation2);
  
  // Check if items collide
  console.log("Items collide:", container.doItemsCollide("ITEM001", "ITEM002"));
  
  // Check item visibility
  console.log("Item1 visible:", container.isItemVisible("ITEM001"));
  console.log("Item2 visible:", container.isItemVisible("ITEM002"));
  
  // Calculate accessibility scores
  console.log("Item1 accessibility:", container.calculateAccessibilityScore("ITEM001").toFixed(2));
  console.log("Item2 accessibility:", container.calculateAccessibilityScore("ITEM002").toFixed(2));
  
  // Find valid placements for a new item
  const item3 = {
    id: "ITEM003",
    name: "Food Container",
    dimensions: new Dimensions(2, 2, 2),
    mass: 3.0,
    priority: "low"
  };
  
  const validPlacements = container.findValidPlacements(item3.dimensions);
  console.log(`Found ${validPlacements.length} valid placements for item3`);
  
  // Place the third item
  if (validPlacements.length > 0) {
    const placement = validPlacements[0];
    container.placeItem(item3, placement.position, placement.orientation);
    
    // Generate a retrieval plan
    const retrievalPlan = container.generateRetrievalPlan("ITEM002");
    console.log("Retrieval plan:", retrievalPlan);
  }
  
  return container;
}

module.exports = {
  Orientation,
  EnhancedSpatialGrid,
  demonstrateBasicOperations
};
