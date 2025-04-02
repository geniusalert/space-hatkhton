// models/Position.ts
/**
 * Represents a coordinate point in 3D space
 */
export class Coordinate {
  constructor(
    public width: number,
    public depth: number,
    public height: number
  ) {}

  /**
   * Creates a copy of the coordinate
   */
  clone(): Coordinate {
    return new Coordinate(this.width, this.depth, this.height);
  }

  /**
   * Calculate the Manhattan distance between two coordinates
   */
  distanceTo(other: Coordinate): number {
    return Math.abs(this.width - other.width) + 
           Math.abs(this.depth - other.depth) + 
           Math.abs(this.height - other.height);
  }
}

/**
 * Represents a position in 3D space with start and end coordinates
 */
export class Position {
  constructor(
    public startCoordinates: Coordinate,
    public endCoordinates: Coordinate
  ) {}

  /**
   * Creates a copy of the position
   */
  clone(): Position {
    return new Position(
      this.startCoordinates.clone(),
      this.endCoordinates.clone()
    );
  }

  /**
   * Check if this position overlaps with another position
   */
  overlaps(other: Position): boolean {
    return !(
      this.endCoordinates.width <= other.startCoordinates.width ||
      this.startCoordinates.width >= other.endCoordinates.width ||
      this.endCoordinates.depth <= other.startCoordinates.depth ||
      this.startCoordinates.depth >= other.endCoordinates.depth ||
      this.endCoordinates.height <= other.startCoordinates.height ||
      this.startCoordinates.height >= other.endCoordinates.height
    );
  }

  /**
   * Calculate the volume of this position
   */
  getVolume(): number {
    const width = this.endCoordinates.width - this.startCoordinates.width;
    const depth = this.endCoordinates.depth - this.startCoordinates.depth;
    const height = this.endCoordinates.height - this.startCoordinates.height;
    return width * depth * height;
  }

  /**
   * Check if this position is visible from the open face (depth = 0)
   */
  isVisibleFromOpenFace(): boolean {
    return this.startCoordinates.depth === 0;
  }

  /**
   * Calculate the distance from the open face of the container
   */
  distanceFromOpenFace(): number {
    return this.startCoordinates.depth;
  }
}

// models/Item.ts
/**
 * Represents a cargo item to be stored in containers
 */
export class Item {
  // Number of times the item has been used
  private usageCount: number = 0;
  
  // Flag to mark if the item is waste
  private isWaste: boolean = false;
  
  // Current container and position where the item is stored
  private currentContainerId: string | null = null;
  private currentPosition: Position | null = null;

  constructor(
    public itemId: string,
    public name: string,
    public width: number,
    public depth: number,
    public height: number,
    public mass: number,
    public priority: number, // 1-100, higher is more critical
    public expiryDate: Date | null, // null if doesn't expire
    public usageLimit: number | null, // null if unlimited uses
    public preferredZone: string
  ) {
    // Validate inputs
    if (priority < 1 || priority > 100) {
      throw new Error("Priority must be between 1 and 100");
    }
    
    if (width <= 0 || depth <= 0 || height <= 0) {
      throw new Error("Dimensions must be positive");
    }
    
    if (mass <= 0) {
      throw new Error("Mass must be positive");
    }
  }

  /**
   * Check if the item has expired based on the current date
   */
  hasExpired(currentDate: Date = new Date()): boolean {
    if (!this.expiryDate) return false;
    return currentDate >= this.expiryDate;
  }

  /**
   * Record usage of the item and check if it's depleted
   * Returns true if the item is now waste after this use
   */
  use(): boolean {
    if (this.isWaste) {
      throw new Error("Cannot use an item that is already waste");
    }
    
    this.usageCount++;
    
    // Check if the item is depleted after this use
    if (this.usageLimit !== null && this.usageCount >= this.usageLimit) {
      this.isWaste = true;
      return true;
    }
    
    return false;
  }

  /**
   * Get the number of remaining uses
   */
  getRemainingUses(): number | null {
    if (this.usageLimit === null) return null;
    return Math.max(0, this.usageLimit - this.usageCount);
  }

  /**
   * Check if the item is considered waste
   */
  checkIfWaste(currentDate: Date = new Date()): boolean {
    if (this.isWaste) return true;
    
    // Check expiry
    if (this.hasExpired(currentDate)) {
      this.isWaste = true;
      return true;
    }
    
    // Check usage limit
    if (this.usageLimit !== null && this.usageCount >= this.usageLimit) {
      this.isWaste = true;
      return true;
    }
    
    return false;
  }

  /**
   * Mark the item as waste with a specific reason
   */
  markAsWaste(reason: string): void {
    this.isWaste = true;
  }

  /**
   * Get waste status
   */
  getWasteStatus(): boolean {
    return this.isWaste;
  }

  /**
   * Set the current container and position of the item
   */
  setLocation(containerId: string, position: Position): void {
    this.currentContainerId = containerId;
    this.currentPosition = position.clone();
  }

  /**
   * Clear the current location when the item is removed
   */
  clearLocation(): void {
    this.currentContainerId = null;
    this.currentPosition = null;
  }

  /**
   * Get the current container ID
   */
  getContainerId(): string | null {
    return this.currentContainerId;
  }

  /**
   * Get the current position
   */
  getPosition(): Position | null {
    return this.currentPosition ? this.currentPosition.clone() : null;
  }

  /**
   * Calculate volume of the item
   */
  getVolume(): number {
    return this.width * this.depth * this.height;
  }

  /**
   * Create possible orientations of the item (6 possible rotations)
   * Returns array of [width, depth, height] tuples for all orientations
   */
  getPossibleOrientations(): number[][] {
    return [
      [this.width, this.depth, this.height],
      [this.width, this.height, this.depth],
      [this.depth, this.width, this.height],
      [this.depth, this.height, this.width],
      [this.height, this.width, this.depth],
      [this.height, this.depth, this.width]
    ];
  }

  /**
   * Create a clone of this item
   */
  clone(): Item {
    const clone = new Item(
      this.itemId,
      this.name,
      this.width,
      this.depth,
      this.height,
      this.mass,
      this.priority,
      this.expiryDate ? new Date(this.expiryDate) : null,
      this.usageLimit,
      this.preferredZone
    );
    
    clone.usageCount = this.usageCount;
    clone.isWaste = this.isWaste;
    clone.currentContainerId = this.currentContainerId;
    
    if (this.currentPosition) {
      clone.currentPosition = this.currentPosition.clone();
    }
    
    return clone;
  }
}

// models/Container.ts
/**
 * Represents a storage container in the space station
 */
export class Container {
  // Map of item IDs to their positions within the container
  private items: Map<string, Item> = new Map();

  constructor(
    public containerId: string,
    public zone: string,
    public width: number,
    public depth: number,
    public height: number
  ) {
    if (width <= 0 || depth <= 0 || height <= 0) {
      throw new Error("Container dimensions must be positive");
    }
  }

  /**
   * Check if a position is within the container's bounds
   */
  isPositionInBounds(position: Position): boolean {
    return (
      position.startCoordinates.width >= 0 &&
      position.startCoordinates.depth >= 0 &&
      position.startCoordinates.height >= 0 &&
      position.endCoordinates.width <= this.width &&
      position.endCoordinates.depth <= this.depth &&
      position.endCoordinates.height <= this.height
    );
  }

  /**
   * Check if a position collides with any items in the container
   */
  positionCollides(position: Position, excludeItemId?: string): boolean {
    for (const [itemId, item] of this.items.entries()) {
      if (excludeItemId && itemId === excludeItemId) continue;
      
      const itemPosition = item.getPosition();
      if (itemPosition && position.overlaps(itemPosition)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Place an item in the container at a specific position
   */
  placeItem(item: Item, position: Position): boolean {
    // Check if position is in bounds
    if (!this.isPositionInBounds(position)) {
      return false;
    }
    
    // Check if position collides with other items
    if (this.positionCollides(position, item.itemId)) {
      return false;
    }
    
    // Place the item
    item.setLocation(this.containerId, position);
    this.items.set(item.itemId, item);
    
    return true;
  }

  /**
   * Remove an item from the container
   */
  removeItem(itemId: string): Item | null {
    const item = this.items.get(itemId);
    if (item) {
      this.items.delete(itemId);
      item.clearLocation();
      return item;
    }
    return null;
  }

  /**
   * Find an item by ID
   */
  getItem(itemId: string): Item | undefined {
    return this.items.get(itemId);
  }

  /**
   * Get all items in the container
   */
  getAllItems(): Map<string, Item> {
    return new Map(this.items);
  }

  /**
   * Calculate the total volume used in the container
   */
  getUsedVolume(): number {
    let totalVolume = 0;
    for (const item of this.items.values()) {
      totalVolume += item.getVolume();
    }
    return totalVolume;
  }

  /**
   * Calculate the total volume of the container
   */
  getTotalVolume(): number {
    return this.width * this.depth * this.height;
  }

  /**
   * Calculate space utilization as a percentage
   */
  getUtilizationPercentage(): number {
    return (this.getUsedVolume() / this.getTotalVolume()) * 100;
  }

  /**
   * Find all items blocking access to a specific item
   * Returns an array of items that need to be moved to retrieve the target item
   */
  findBlockingItems(targetItemId: string): Item[] {
    const targetItem = this.items.get(targetItemId);
    if (!targetItem) return [];
    
    const targetPosition = targetItem.getPosition();
    if (!targetPosition) return [];
    
    const blockingItems: Item[] = [];
    
    // For each item, check if it blocks the path from the open face to the target item
    for (const [itemId, item] of this.items.entries()) {
      if (itemId === targetItemId) continue;
      
      const itemPosition = item.getPosition();
      if (!itemPosition) continue;
      
      // An item blocks the target if:
      // 1. It has some overlap in width and height with the target
      // 2. It has a lower depth value (closer to the open face)
      const widthOverlap = !(
        itemPosition.endCoordinates.width <= targetPosition.startCoordinates.width ||
        itemPosition.startCoordinates.width >= targetPosition.endCoordinates.width
      );
      
      const heightOverlap = !(
        itemPosition.endCoordinates.height <= targetPosition.startCoordinates.height ||
        itemPosition.startCoordinates.height >= targetPosition.endCoordinates.height
      );
      
      const isInFront = itemPosition.startCoordinates.depth < targetPosition.startCoordinates.depth;
      
      if (widthOverlap && heightOverlap && isInFront) {
        blockingItems.push(item);
      }
    }
    
    return blockingItems;
  }

  /**
   * Find all visible positions of a given size
   * A position is visible if it's directly accessible from the open face
   */
  findVisiblePositions(width: number, height: number, depth: number): Position[] {
    const positions: Position[] = [];
    
    // Try each possible position along the open face
    for (let w = 0; w <= this.width - width; w++) {
      for (let h = 0; h <= this.height - height; h++) {
        const position = new Position(
          new Coordinate(w, 0, h),
          new Coordinate(w + width, depth, h + height)
        );
        
        if (!this.positionCollides(position)) {
          positions.push(position);
        }
      }
    }
    
    return positions;
  }

  /**
   * Clone this container with all its items
   */
  clone(): Container {
    const clonedContainer = new Container(
      this.containerId,
      this.zone,
      this.width,
      this.depth,
      this.height
    );
    
    // Clone all items and their positions
    for (const item of this.items.values()) {
      const clonedItem = item.clone();
      const position = item.getPosition();
      
      if (position) {
        clonedContainer.placeItem(clonedItem, position);
      }
    }
    
    return clonedContainer;
  }
}
