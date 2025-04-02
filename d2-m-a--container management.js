/**
 * Container Management for Space Cargo System
 * 
 * This module implements:
 * - Advanced add/remove item functions for containers
 * - Methods to check space availability
 * - Functions to calculate container utilization and metrics
 */

const { Position, Dimensions } = require('./spatial-grid-implementation');
const { Orientation, EnhancedSpatialGrid } = require('./basic-operations');

/**
 * Container class that extends EnhancedSpatialGrid with advanced management features
 */
class Container extends EnhancedSpatialGrid {
  constructor(id, dimensions, zone = "general", openFace = "front") {
    super(dimensions, openFace);
    
    this.id = id;
    this.zone = zone;
    this.totalVolume = dimensions.width * dimensions.depth * dimensions.height;
    this.usedVolume = 0;
    
    // Keep track of items by priority
    this.priorityItems = {
      high: new Set(),
      medium: new Set(),
      low: new Set()
    };
    
    // Keep track of items by expiry date
    this.itemsByExpiry = new Map(); // Maps expiry date string to set of item IDs
    
    // Keep track of access history
    this.accessHistory = [];
  }
  
  /**
   * Add an item to the container with optimal positioning
   * @param {Object} item - The item object with all properties
   * @param {Object} options - Optional parameters for placement
   * @returns {Object} Placement information or null if placement failed
   */
  addItem(item, options = {}) {
    // Default options
    const defaultOptions = {
      prioritizeAccessibility: true, // If true, place for best accessibility
      preferredOrientation: null,    // Specific orientation to try first
      preferredPosition: null,       // Specific position to try first
      useRecommendation: true        // If true, use container's recommendation
    };
    
    const opts = { ...defaultOptions, ...options };
    
    // Validate the item object
    if (!item.id || !item.dimensions || !item.priority) {
      throw new Error("Item must have id, dimensions, and priority properties");
    }
    
    // Check if this item is already in the container
    if (this.itemsData.has(item.id)) {
      throw new Error(`Item with ID ${item.id} is already in the container`);
    }
    
    // If preferred orientation and position are provided, try that first
    if (opts.preferredOrientation && opts.preferredPosition) {
      const effectiveDims = opts.preferredOrientation.getEffectiveDimensions(item.dimensions);
      if (this.isSpaceFree(opts.preferredPosition, effectiveDims)) {
        const success = this.placeItem(item, opts.preferredPosition, opts.preferredOrientation);
        if (success) {
          // Update container metrics
          this.updateContainerMetricsAfterAdd(item);
          
          return {
            success: true,
            position: opts.preferredPosition,
            orientation: opts.preferredOrientation
          };
        }
      }
    }
    
    // Find all valid placements
    const validPlacements = this.findValidPlacements(item.dimensions);
    
    if (validPlacements.length === 0) {
      return { success: false, reason: "No valid placement found" };
    }
    
    // Handle placement based on options
    let bestPlacement;
    
    if (opts.prioritizeAccessibility) {
      // Find the placement with the best accessibility score
      bestPlacement = this.findBestAccessiblePlacement(validPlacements, item);
    } else if (opts.useRecommendation) {
      // Find the optimal placement based on container's recommendation algorithm
      bestPlacement = this.recommendPlacement(validPlacements, item);
    } else {
      // Just use the first valid placement
      bestPlacement = validPlacements[0];
    }
    
    // Place the item
    const success = this.placeItem(item, bestPlacement.position, bestPlacement.orientation);
    
    if (success) {
      // Update container metrics
      this.updateContainerMetricsAfterAdd(item);
      
      return {
        success: true,
        position: bestPlacement.position,
        orientation: bestPlacement.orientation
      };
    }
    
    return { success: false, reason: "Failed to place item" };
  }
  
  /**
   * Update container metrics after adding an item
   */
  updateContainerMetricsAfterAdd(item) {
    // Add to priority tracking
    if (this.priorityItems[item.priority]) {
      this.priorityItems[item.priority].add(item.id);
    }
    
    // Add to expiry tracking if applicable
    if (item.expiryDate) {
      const expiryStr = item.expiryDate.toISOString().split('T')[0];
      if (!this.itemsByExpiry.has(expiryStr)) {
        this.itemsByExpiry.set(expiryStr, new Set());
      }
      this.itemsByExpiry.get(expiryStr).add(item.id);
    }
    
    // Update used volume
    const volume = item.dimensions.width * item.dimensions.depth * item.dimensions.height;
    this.usedVolume += volume;
  }
  
  /**
   * Remove an item from the container
   * @param {string} itemId - The ID of the item to remove
   * @returns {Object} The removed item data and success status
   */
  removeItem(itemId) {
    if (!this.itemsData.has(itemId)) {
      return { success: false, reason: `Item with ID ${itemId} not found` };
    }
    
    // Get the item data before removal
    const itemData = this.itemsData.get(itemId);
    
    // Check if the item can be directly accessed
    const isAccessible = this.isItemAccessible(itemId);
    
    if (!isAccessible) {
      // Generate retrieval plan
      const plan = this.generateRetrievalPlan(itemId);
      
      return {
        success: false,
        reason: "Item is not directly accessible",
        retrievalPlan: plan
      };
    }
    
    // Remove the item
    this.releaseSpace(itemId);
    
    // Update container metrics
    this.updateContainerMetricsAfterRemove(itemData);
    
    // Record this access in history
    this.recordAccess(itemId, "remove");
    
    return {
      success: true,
      item: itemData
    };
  }
  
  /**
   * Update container metrics after removing an item
   */
  updateContainerMetricsAfterRemove(itemData) {
    // Remove from priority tracking
    if (this.priorityItems[itemData.priority]) {
      this.priorityItems[itemData.priority].delete(itemData.id);
    }
    
    // Remove from expiry tracking if applicable
    if (itemData.expiryDate) {
      const expiryStr = itemData.expiryDate.toISOString().split('T')[0];
      if (this.itemsByExpiry.has(expiryStr)) {
        this.itemsByExpiry.get(expiryStr).delete(itemData.id);
        if (this.itemsByExpiry.get(expiryStr).size === 0) {
          this.itemsByExpiry.delete(expiryStr);
        }
      }
    }
    
    // Update used volume
    const volume = itemData.dimensions.width * itemData.dimensions.depth * itemData.dimensions.height;
    this.usedVolume -= volume;
  }
  
  /**
   * Record an access operation in the container's history
   */
  recordAccess(itemId, operation) {
    this.accessHistory.push({
      timestamp: new Date(),
      itemId,
      operation
    });
  }
  
  /**
   * Check if an item is directly accessible (visible and not blocked)
   */
  isItemAccessible(itemId) {
    return this.isItemVisible(itemId) && this.findBlockingItems(itemId).length === 0;
  }
  
  /**
   * Find the best placement for accessibility
   */
  findBestAccessiblePlacement(placements, item) {
    let bestScore = -1;
    let bestPlacement = null;
    
    // Temporarily place the item at each position and calculate accessibility
    for (const placement of placements) {
      // Create a copy of the container to simulate placement
      const tempContainer = this.createTempContainerWithPlacement(
        item, placement.position, placement.orientation
      );
      
      // Calculate accessibility score
      const score = tempContainer.calculateAccessibilityScore(item.id);
      
      if (score > bestScore) {
        bestScore = score;
        bestPlacement = placement;
      }
    }
    
    return bestPlacement;
  }
  
  /**
   * Create a temporary container with an item placed at a specific position
   */
  createTempContainerWithPlacement(item, position, orientation) {
    // Create a new container with same dimensions
    const tempContainer = new Container(
      "temp", this.dimensions, this.zone, this.openFace
    );
    
    // Copy all existing items
    for (const [itemId, itemData] of this.itemsData.entries()) {
      tempContainer.placeItem(
        {...itemData}, 
        itemData.position, 
        itemData.orientation
      );
    }
    
    // Place the new item
    tempContainer.placeItem(item, position, orientation);
    
    return tempContainer;
  }
  
  /**
   * Recommend optimal placement based on container's algorithm
   * (This is a more sophisticated placement algorithm)
   */
  recommendPlacement(placements, item) {
    // This is where a more advanced algorithm could be implemented
    // For now, we'll use some heuristics:
    
    const scoredPlacements = placements.map(placement => {
      // Create a temp container to evaluate this placement
      const tempContainer = this.createTempContainerWithPlacement(
        item, placement.position, placement.orientation
      );
      
      // Score factors:
      
      // 1. Accessibility score (0-100)
      const accessibilityScore = tempContainer.calculateAccessibilityScore(item.id);
      
      // 2. Space utilization score (0-100)
      // Prefer placements that keep large contiguous empty spaces
      const beforeLargestSpace = this.findLargestEmptySpace();
      const afterLargestSpace = tempContainer.findLargestEmptySpace();
      
      let utilizationScore = 100;
      if (beforeLargestSpace) {
        const beforeVolume = beforeLargestSpace.dimensions.width * 
                            beforeLargestSpace.dimensions.depth * 
                            beforeLargestSpace.dimensions.height;
                            
        const afterVolume = afterLargestSpace ? 
          afterLargestSpace.dimensions.width * 
          afterLargestSpace.dimensions.depth * 
          afterLargestSpace.dimensions.height : 0;
        
        // Penalize significant fragmentation of empty space
        utilizationScore = Math.min(100, (afterVolume / beforeVolume) * 100);
      }
      
      // 3. Distance to compatible items score (0-100)
      // If zone preferences exist, prefer placements near compatible items
      let compatibilityScore = 50; // Neutral score by default
      
      if (item.preferredZone) {
        // Find closest item of the same preferred zone
        let minDistance = Infinity;
        
        for (const [otherId, otherItem] of this.itemsData.entries()) {
          if (otherItem.preferredZone === item.preferredZone) {
            const distance = this.calculateDistance(
              placement.position, otherItem.position
            );
            minDistance = Math.min(minDistance, distance);
          }
        }
        
        // Convert distance to a score (closer = higher score)
        if (minDistance !== Infinity) {
          // Max possible distance in container
          const maxDist = Math.sqrt(
            Math.pow(this.dimensions.width, 2) + 
            Math.pow(this.dimensions.depth, 2) + 
            Math.pow(this.dimensions.height, 2)
          );
          
          compatibilityScore = 100 - ((minDistance / maxDist) * 100);
        }
      }
      
      // 4. Priority adjustment based on item properties
      let priorityMultiplier = 1.0;
      
      // High priority items should be more accessible
      if (item.priority === "high") {
        priorityMultiplier = 1.5;
      } else if (item.priority === "low") {
        priorityMultiplier = 0.8;
      }
      
      // Items with expiry dates should be more accessible
      if (item.expiryDate) {
        const now = new Date();
        const expiry = new Date(item.expiryDate);
        const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24);
        
        if (daysUntilExpiry < 30) {
          priorityMultiplier += 0.5;
        }
      }
      
      // Calculate final score with weighted components
      const weightedScore = (
        (accessibilityScore * 0.5) +  // 50% weight to accessibility
        (utilizationScore * 0.3) +    // 30% weight to space utilization
        (compatibilityScore * 0.2)    // 20% weight to zone compatibility
      ) * priorityMultiplier;
      
      return {
        placement,
        score: weightedScore
      };
    });
    
    // Sort by score (highest first) and take the best one
    scoredPlacements.sort((a, b) => b.score - a.score);
    return scoredPlacements[0].placement;
  }
  
  /**
   * Calculate Euclidean distance between two positions
   */
  calculateDistance(pos1, pos2) {
    return Math.sqrt(
      Math.pow(pos2.x - pos1.x, 2) +
      Math.pow(pos2.y - pos1.y, 2) +
      Math.pow(pos2.z - pos1.z, 2)
    );
  }
  
  /**
   * Check space availability for an item with specific dimensions
   * @returns {Object} Availability information and recommendations
   */
  checkSpaceAvailability(itemDimensions) {
    // Find all possible orientations and placements
    const validPlacements = this.findValidPlacements(itemDimensions);
    
    if (validPlacements.length === 0) {
      return {
        available: false,
        reason: "No valid placement found for the given dimensions",
        recommendation: this.suggestDimensionAdjustment(itemDimensions)
      };
    }
    
    // Find the largest empty space
    const largestSpace = this.findLargestEmptySpace();
    
    // Calculate the volume of the item
    const itemVolume = itemDimensions.width * itemDimensions.depth * itemDimensions.height;
    
    // Calculate the free volume in the container
    const freeVolume = this.totalVolume - this.usedVolume;
    
    return {
      available: true,
      validPlacementsCount: validPlacements.length,
      recommendedPlacement: validPlacements[0],
      largestEmptySpace: largestSpace,
      itemVolume: itemVolume,
      freeVolume: freeVolume,
      containerUtilization: this.getUtilizationPercentage()
    };
  }
  
  /**
   * Suggest dimension adjustments if an item doesn't fit
   */
  suggestDimensionAdjustment(itemDimensions) {
    // Find the largest empty space
    const largestSpace = this.findLargestEmptySpace();
    
    if (!largestSpace) {
      return "Container is completely full";
    }
    
    const maxDims = largestSpace.dimensions;
    
    return {
      message: "Item dimensions are too large for available spaces",
      largestAvailableSpace: maxDims,
      suggestedAdjustment: {
        width: Math.min(itemDimensions.width, maxDims.width),
        depth: Math.min(itemDimensions.depth, maxDims.depth),
        height: Math.min(itemDimensions.height, maxDims.height)
      }
    };
  }
  
  /**
   * Get detailed container utilization metrics
   */
  getContainerUtilization() {
    // Basic utilization percentage
    const volumeUtilization = (this.usedVolume / this.totalVolume) * 100;
    
    // Count items by priority
    const itemCounts = {
      high: this.priorityItems.high.size,
      medium: this.priorityItems.medium.size,
      low: this.priorityItems.low.size,
      total: this.itemsData.size
    };
    
    // Calculate accessibility metrics
    const accessibilityMetrics = this.calculateAccessibilityMetrics();
    
    // Find items that will expire soon
    const expiringItems = this.findExpiringItems(30); // Items expiring in next 30 days
    
    // Space fragmentation analysis
    const fragmentationAnalysis = this.analyzeSpaceFragmentation();
    
    return {
      container: {
        id: this.id,
        zone: this.zone,
        dimensions: this.dimensions,
        totalVolume: this.totalVolume,
        openFace: this.openFace
      },
      utilization: {
        usedVolume: this.usedVolume,
        freeVolume: this.totalVolume - this.usedVolume,
        percentUtilized: volumeUtilization.toFixed(2),
        itemCount: itemCounts
      },
      accessibility: accessibilityMetrics,
      fragmentation: fragmentationAnalysis,
      expiring: {
        next30Days: expiringItems.length,
        items: expiringItems
      },
      recommendations: this.generateOptimizationRecommendations()
    };
  }
  
  /**
   * Calculate accessibility metrics for all items
   */
  calculateAccessibilityMetrics() {
    const scores = [];
    let lowAccessibilityItems = 0;
    
    for (const itemId of this.itemsData.keys()) {
      const score = this.calculateAccessibilityScore(itemId);
      scores.push(score);
      
      if (score < 40) { // Threshold for "low accessibility"
        lowAccessibilityItems++;
      }
    }
    
    // Calculate average and distribution
    const avgScore = scores.length > 0 ? 
      scores.reduce((sum, score) => sum + score, 0) / scores.length : 0;
    
    return {
      averageAccessibility: avgScore.toFixed(2),
      lowAccessibilityCount: lowAccessibilityItems,
      highPriorityLowAccess: this.countHighPriorityLowAccessibility()
    };
  }
  
  /**
   * Count high priority items with low accessibility
   */
  countHighPriorityLowAccessibility() {
    let count = 0;
    
    for (const itemId of this.priorityItems.high) {
      const score = this.calculateAccessibilityScore(itemId);
      if (score < 40) {
        count++;
      }
    }
    
    return count;
  }
  
  /**
   * Find items that will expire within a certain number of days
   */
  findExpiringItems(days) {
    const expiringItems = [];
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() + days);
    
    for (const [expiryStr, itemIds] of this.itemsByExpiry.entries()) {
      const expiryDate = new Date(expiryStr);
      
      if (expiryDate <= cutoffDate) {
        for (const itemId of itemIds) {
          const item = this.itemsData.get(itemId);
          expiringItems.push({
            id: itemId,
            name: item.name,
            expiryDate: expiryStr,
            accessibility: this.calculateAccessibilityScore(itemId)
          });
        }
      }
    }
    
    // Sort by expiry date (soonest first)
    expiringItems.sort((a, b) => new Date(a.expiryDate) - new Date(b.expiryDate));
    
    return expiringItems;
  }
  
  /**
   * Analyze how fragmented the free space is
   */
  analyzeSpaceFragmentation() {
    const emptySpaces = [];
    let totalEmptyVolume = 0;
    
    // Use a simplified algorithm to find empty spaces
    // A more advanced algorithm would use a 3D flood fill
    
    // Start with the largest space
    let largestSpace = this.findLargestEmptySpace();
    
    // Keep finding spaces until we've accounted for all free volume
    while (largestSpace && totalEmptyVolume < (this.totalVolume - this.usedVolume)) {
      const spaceVolume = largestSpace.dimensions.width * 
                          largestSpace.dimensions.depth * 
                          largestSpace.dimensions.height;
      
      emptySpaces.push({
        position: largestSpace.position,
        dimensions: largestSpace.dimensions,
        volume: spaceVolume
      });
      
      totalEmptyVolume += spaceVolume;
      
      // Temporarily mark this space as occupied to find the next largest space
      this.temporarilyOccupySpace(largestSpace.position, largestSpace.dimensions);
      largestSpace = this.findLargestEmptySpace();
      
      // Limit the number of spaces we find to avoid infinite loops
      if (emptySpaces.length > 10) break;
    }
    
    // Restore the container state
    this.restoreTemporaryState();
    
    // Calculate fragmentation index (ratio of largest space to free volume)
    const largestEmptyVolume = emptySpaces.length > 0 ? emptySpaces[0].volume : 0;
    const fragmentationIndex = largestEmptyVolume / (this.totalVolume - this.usedVolume);
    
    return {
      fragmentationIndex: fragmentationIndex.toFixed(2),
      largestEmptyVolume,
      emptySpaces: emptySpaces.length,
      contiguousSpaces: emptySpaces
    };
  }
  
  /**
   * Temporarily mark a space as occupied for analysis
   */
  temporarilyOccupySpace(position, dimensions) {
    if (!this._tempState) {
      // Save current state
      this._tempState = JSON.parse(JSON.stringify(this.grid));
    }
    
    // Mark space as occupied with a special marker
    for (let x = position.x; x < position.x + dimensions.width; x++) {
      for (let y = position.y; y < position.y + dimensions.depth; y++) {
        for (let z = position.z; z < position.z + dimensions.height; z++) {
          if (this.isWithinBounds(new Position(x, y, z))) {
            this.grid[x][y][z] = "TEMP_OCCUPIED";
          }
        }
      }
    }
  }
  
  /**
   * Restore container state after temporary modifications
   */
  restoreTemporaryState() {
    if (this._tempState) {
      this.grid = JSON.parse(JSON.stringify(this._tempState));
      this._tempState = null;
    }
  }
  
  /**
   * Generate optimization recommendations for container usage
   */
  generateOptimizationRecommendations() {
    const recommendations = [];
    
    // Check for high priority items with low accessibility
    if (this.countHighPriorityLowAccessibility() > 0) {
      recommendations.push({
        type: "accessibility",
        priority: "high",
        message: "Consider reorganizing to improve access to high priority items"
      });
    }
    
    // Check for expiring items with low accessibility
    const expiringItems = this.findExpiringItems(30);
    const lowAccessExpiringItems = expiringItems.filter(item => item.accessibility < 40);
    
    if (lowAccessExpiringItems.length > 0) {
      recommendations.push({
        type: "expiry",
        priority: "high",
        message: `${lowAccessExpiringItems.length} expiring items have poor accessibility`
      });
    }
    
    // Check fragmentation
    const fragmentation = this.analyzeSpaceFragmentation();
    if (parseFloat(fragmentation.fragmentationIndex) < 0.5 && this.getUtilizationPercentage() < 80) {
      recommendations.push({
        type: "fragmentation",
        priority: "medium",
        message: "Space is heavily fragmented. Consider reorganization to consolidate free space"
      });
    }
    
    // Check utilization
    if (this.getUtilizationPercentage() > 90) {
      recommendations.push({
        type: "utilization",
        priority: "medium",
        message: "Container is nearing capacity. Consider transferring items or expanding storage"
      });
    }
    
    return recommendations;
  }
}

// Example usage
function demonstrateContainerManagement() {
  // Create a container
  const containerDims = new Dimensions(10, 8, 5);
  const container = new Container("CONT001", containerDims, "science", "front");
  
  // Create some items
  const items = [
    {
      id: "ITEM001",
      name: "Medical Supplies",
      dimensions: new Dimensions(3, 2, 2),
      mass: 2.5,
      priority: "high",
      expiryDate: new Date("2025-06-15")
    },
    {
      id: "ITEM002",
      name: "Food Rations",
      dimensions: new Dimensions(2, 3, 1),
      mass: 4.0,
      priority: "high",
      expiryDate: new Date("2025-05-01")
    },
    {
      id: "ITEM003",
      name: "Science Equipment",
      dimensions: new Dimensions(4, 3, 2),
      mass: 7.5,
      priority: "medium",
      preferredZone: "science"
    },
    {
      id: "ITEM004",
      name: "Spare Parts",
      dimensions: new Dimensions(2, 2, 1),
      mass: 3.0,
      priority: "low"
    }
  ];
  
  // Add items to container
  for (const item of items) {
    const result = container.addItem(item, { prioritizeAccessibility: true });
    console.log(`Added ${item.name}: ${result.success ? "Success" : "Failed"}`);
  }
  
  // Check space availability for a new item
  const newItemDims = new Dimensions(3, 3, 3);
  const availability = container.checkSpaceAvailability(newItemDims);
  console.log("Space availability:", availability.available);
  
  // Get container utilization metrics
  const utilization = container.getContainerUtilization();
  console.log(`Container utilization: ${utilization.utilization.percentUtilized}%`);
  console.log(`Average accessibility: ${utilization.accessibility.averageAccessibility}`);
  
  // Try to remove an item
  const removalResult = container.removeItem("ITEM002");
  if (removalResult.success) {
    console.log("Item removed successfully");
  } else {
    console.log("Item removal failed:", removalResult.reason);
    console.log("Retrieval plan:", removalResult.retrievalPlan);
  }
  
  return container;
}

module.exports = {
  Container,
  demonstrateContainerManagement
};