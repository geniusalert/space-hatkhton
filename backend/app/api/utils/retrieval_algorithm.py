from typing import List, Dict

def get_blocking_items(target_item: Dict, all_items: List[Dict]) -> List[Dict]:
    """
    Identify items blocking the target item from being retrieved.
    - Assumes retrieval occurs along the depth axis (front to back).
    """
    blocking_items = []
    for item in all_items:
        if item["itemId"] != target_item["itemId"]:
            # Check if the item is in front of the target and overlaps in width/height
            if (item["startD"] < target_item["startD"] and
                item["startW"] < target_item["endW"] and item["endW"] > target_item["startW"] and
                item["startH"] < target_item["endH"] and item["endH"] > target_item["startH"]):
                blocking_items.append(item)
    return blocking_items

def calculate_retrieval_steps(target_item: Dict, container_items: List[Dict]) -> List[Dict]:
    """
    Calculate the steps to retrieve the target item.
    - Remove blocking items, retrieve the target, then place back the removed items.
    """
    steps = []
    blocking_items = get_blocking_items(target_item, container_items)
    
    # Step 1: Remove all blocking items
    for item in blocking_items:
        steps.append({
            "action": "remove",
            "itemId": item["itemId"],
            "itemName": item["name"]
        })
    
    # Step 2: Retrieve the target item
    steps.append({
        "action": "retrieve",
        "itemId": target_item["itemId"],
        "itemName": target_item["name"]
    })
    
    # Step 3: Place back the removed items in reverse order
    for item in reversed(blocking_items):
        steps.append({
            "action": "placeBack",
            "itemId": item["itemId"],
            "itemName": item["name"]
        })
    
    return steps