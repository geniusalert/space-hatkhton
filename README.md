
# Cargo Management System for Space Station



This repo deals with building a assistant for cargo management system for international space station while considring these following parameters 
1. Efficient Placement of Items
2. Quick Retrieval of Items
3. Rearrangement Optimization
4. Waste Disposal Management
5. Cargo Return Planning
6. Logging


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
4. 
