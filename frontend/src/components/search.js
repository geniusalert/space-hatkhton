import React, { useState } from 'react';
import { searchItem } from '../api';

const Search = () => {
  const [itemId, setItemId] = useState('');
  const [itemName, setItemName] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    setError(null);
    setResult(null);
    if (!itemId && !itemName) {
      setError('Please enter an Item ID or Name');
      return;
    }

    try {
      const response = await searchItem(itemId || null, itemName || null, 'astronaut1'); // Hardcoded userId for demo
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while searching');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Search Item</h2>
      <div style={{ marginBottom: '10px' }}>
        <input
          type="text"
          value={itemId}
          onChange={(e) => setItemId(e.target.value)}
          placeholder="Item ID"
          style={{ marginRight: '10px', padding: '5px' }}
        />
        <input
          type="text"
          value={itemName}
          onChange={(e) => setItemName(e.target.value)}
          placeholder="Item Name"
          style={{ marginRight: '10px', padding: '5px' }}
        />
        <button onClick={handleSearch} style={{ padding: '5px 10px' }}>
          Search
        </button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}
      {result && (
        <div>
          {result.found ? (
            <div>
              <h3>Item Found</h3>
              <p><strong>ID:</strong> {result.item.itemId}</p>
              <p><strong>Name:</strong> {result.item.name}</p>
              <p><strong>Container:</strong> {result.item.containerId} ({result.item.zone})</p>
              <p><strong>Position:</strong> 
                ({result.item.position.startCoordinates.width}, 
                 {result.item.position.startCoordinates.depth}, 
                 {result.item.position.startCoordinates.height}) - 
                ({result.item.position.endCoordinates.width}, 
                 {result.item.position.endCoordinates.depth}, 
                 {result.item.position.endCoordinates.height})
              </p>
              <h4>Retrieval Steps:</h4>
              <ul>
                {result.item.retrievalSteps.map((step, index) => (
                  <li key={index}>
                    Step {step.step}: {step.action} {step.itemName} (ID: {step.itemId})
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p>No item found</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Search;