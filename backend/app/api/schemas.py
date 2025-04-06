from pydantic import BaseModel

class RetrieveRequest(BaseModel):
    itemId: str
    userId: str
    timestamp: str  # Expected in ISO format, e.g., "2023-10-25T12:00:00Z"