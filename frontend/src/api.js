import axios from 'axios';

// Base URL for the backend API (adjust if running in Docker or different environment)
const API_URL = 'http://localhost:8000';

// Search for an item by ID or name
export const searchItem = async (itemId, itemName, userId) => {
  const params = {};
  if (itemId) params.itemId = itemId;
  if (itemName) params.itemName = itemName;
  if (userId) params.userId = userId;

  return axios.get(`${API_URL}/api/search`, { params });
};

// Retrieve an item
export const retrieveItem = async (itemId, userId, timestamp) => {
  const data = {
    itemId,
    userId,
    timestamp,
  };
  return axios.post(`${API_URL}/api/retrieve`, data);
};