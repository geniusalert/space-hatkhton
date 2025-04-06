from typing import List, Dict

def get_blocking_items(target_item: Dict, all_items: List[Dict], axis: str = "depth") -> List[Dict]:
    blocking_items = []
    for item in all_items:
        if item["itemId"] != target_item["itemId"]:
            if axis == "depth":
                if (item["startD"] < target_item["startD"] and
                    item["startW"] < target_item["endW"] and item["endW"] > target_item["startW"] and
                    item["startH"] < target_item["endH"] and item["endH"] > target_item["startH"]):
                    blocking_items.append(item)
            # Add conditions for other axes if needed
    return blocking_items

def calculate_retrieval_steps(target_item: Dict, container_items: List[Dict], axis: str = "depth") -> List[Dict]:
    steps = []
    blocking_items = get_blocking_items(target_item, container_items, axis)
    for item in blocking_items:
        steps.append({"action": "remove", "itemId": item["itemId"], "itemName": item["name"]})
    steps.append({"action": "retrieve", "itemId": target_item["itemId"], "itemName": target_item["name"]})
    for item in reversed(blocking_items):
        steps.append({"action": "placeBack", "itemId": item["itemId"], "itemName": item["name"]})
    return steps