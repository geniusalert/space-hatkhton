
# Cargo Management System for Space Station



This repo deals with building a assistant for cargo management system for international space station while considring these following parameters 
1. Efficient Placement of Items
2. Quick Retrieval of Items
3. Rearrangement Optimization
4. Waste Disposal Management
5. Cargo Return Planning
6. Logging


![Screenshot (52)](https://github.com/user-attachments/assets/cc6b35aa-a86a-43fc-a6f5-8ff6e9ae9369)


# Getting started

To set up and run the Space Station Cargo Management System API locally, follow these steps: 

1. Clone the Repository



```bash
git clone geniusalert/space-hatkhton
```
    
2. Build the Docker Container:

```bash
docker build -t cargo-management .
```
3. Run the Container


```bash
docker run -p 8000:8000 cargo-management
```
4. Test the API

```bash
curl -X POST "http://localhost:8000/api/placement" -H "Content-Type: application/json" -d '{"items":[{"itemId":"item-1","name":"Example Item","width":10,"depth":10,"height":10,"mass":1,"priority":1,"preferredZone":"A"}],"containers":[{"containerId":"container-1","zone":"A","width":100,"depth":100,"height":100}]}'
```
## API Documentation
This section documents all the APIs implemented in the Space Station Cargo Management System, fulfilling the hackathon requirements.

1. Placement API
Endpoint: POST /api/placement

Description: Places items into containers based on a placement algorithm, storing their positions in the database.

Request: 

```bash
{
  "items": [
    {
      "itemId": "item-1",
      "name": "Example Item",
      "width": 10,
      "depth": 10,
      "height": 10,
      "mass": 1,
      "priority": 1,
      "preferredZone": "A"
    }
  ],
  "containers": [
    {
      "containerId": "container-1",
      "zone": "A",
      "width": 100,
      "depth": 100,
      "height": 100
    }
  ]
}
```
2. Search API
Endpoint: GET /api/search

Description: Searches for an item by ID and returns its details, including container location and retrieval steps.

Request:

Query Parameter: itemId (required, string) Example: http://localhost:8000/api/search?itemId=item-1
Response:

```bash
{
  "success": true,
  "found": true,
  "item": {
    "itemId": "item-1",
    "name": "Example Item",
    "containerId": "container-1",
    "zone": "A",
    "position": {
      "startCoordinates": {"width": 0, "depth": 0, "height": 0},
      "endCoordinates": {"width": 10, "depth": 10, "height": 10}
    },
    "retrievalSteps": [
      {"action": "retrieve", "itemId": "item-1", "itemName": "Example Item"}
 }
}  "items": [
    {
      "itemId": "item-1",
      "name": "Example Item",
      "width": 10,
      "depth": 10,
      "height": 10,
      "mass": 1,
      "priority": 1,
      "preferredZone": "A"
    }
  ],
  "containers": [
    {
      "containerId": "container-1",
      "zone": "A",
      "width": 100,
      "depth": 100,
      "height": 100
    }
  ]
}
```    
 

3. Retrive api 
Endpoint: POST /api/retrieve

Description: Retrieves an item, decrements its usage limit, and logs the action.

Request:

```bash
{
  "itemId": "item-1",
  "userId": "user-1",
  "timestamp": "2025-04-06T12:00:00Z"
}
```    
4. Waste Management APIs
Identify Waste
Endpoint: GET /api/waste/identify

Description: Identifies items that are expired or have no remaining uses.

Request: No body required.

Response:

```bash
{
  "success": true,
  "wasteItems": [
    {
      "itemId": "item-1",
      "name": "Example Item",
      "reason": "Expired",
      "containerId": "container-1"
    }
  ]
}
```    
4. Waste Return Plan
Endpoint: POST /api/waste/return-plan

Description: Plans moving waste items to an undocking container, respecting a weight limit.

Request:

Query Parameters: undockingContainerId (string), undockingDate (string, ISO format), maxWeight (float) Example: http://localhost:8000/api/waste/return-plan?undockingContainerId=container-2&undockingDate=2025-04-07T00:00:00Z&maxWeight=10
Response:
```bash
{
  "success": true,
  "wasteItems": [
    {
      "itemId": "item-1",
      "name": "Example Item",
      "reason": "Expired",
      "containerId": "container-1"
    }
  ]
}
```    
5. Time Simulation API
Endpoint: POST /api/simulate/day

Description: Simulates time progression by a specified number of days, updating usage limits.

Request:
```bash
{
  "days": 5
}
```    
6. Import/Export APIs
Import Items
Endpoint: POST /api/import/items

Description: Imports items from a CSV file.

Request:

Form Data: file (CSV file with headers matching Item schema)
Response:
```bash
{
  "success": true,
  "itemsImported": 1,
  "errors": []
}
```
7. Import Containers
Endpoint: POST /api/import/containers

Description: Imports containers from a CSV file.

Request:

Form Data: file (CSV file with headers matching Container schema)
Response:
```bash
{
  "success": true,
  "containersImported": 1,
  "errors": []
}
```
8. Export Arrangement
Endpoint: GET /api/export/arrangement

Description: Exports the current item arrangement as a CSV file.

Request: No body required.

Response: A downloadable CSV file with content like:

Item ID,Container ID,Start Coordinates,End Coordinates
item-1,container-1,(0,0,0),(10,10,10)

8. Logging API
Endpoint: GET /api/logs

Description: Retrieves logs with optional filters.

Request:

Query Parameters (all optional): startDate, endDate, itemId, userId, actionType Example: http://localhost:8000/api/logs?startDate=2025-04-06T00:00:00Z&actionType=retrieval
Response:
```bash
{
  "success": true,
  "logs": [
    {
      "timestamp": "2025-04-06T12:00:00Z",
      "userId": "user-1",
      "actionType": "retrieval",
      "itemId": "item-1",
      "details": "{\"action\": \"retrieval\", \"userId\": \"user-1\", \"timestamp\": \"2025-04-06T12:00:00Z\", \"itemId\": \"item-1\"}"
    }
  ]
}
```
Required Features
The solution implements all required APIs as specified in the hackathon problem statement:

✅ Placement API: Enhanced from the sample with database persistence.
✅ Search API: Finds items and provides retrieval steps.
✅ Retrieve API: Updates usage limits and logs actions.
✅ Waste Management APIs: Identifies and plans waste return.
✅ Time Simulation API: Simulates time progression.
✅ Import/Export APIs: Handles CSV-based data import/export.
✅ Logging API: Retrieves action logs with filtering.
