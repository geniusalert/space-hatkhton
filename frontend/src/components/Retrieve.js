import React, { useState } from 'react';
import { retrieveItem } from '../api';

const Retrieve = () => {
  const [itemId, setItemId] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRetrieve = async () => {
    setError(null);
    setResult(null);
    if (!itemId) {
      setError('Please enter an Item ID');
      return;
    }

    try {
      const timestamp = new Date().toISOString(); // Current time in ISO format
      const response = await retrieveItem(itemId, 'astronaut1', timestamp); // Hardcoded userId
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while retrieving');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Retrieve Item</h2>
      <div style={{ marginBottom: '10px' }}>
        <input
          type="text"
          value={itemId}
          onChange={(e) => setItemId(e.target.value)}
          placeholder="Item ID"
          style={{ marginRight: '10px', padding: '5px' }}
        />
        <button onClick={handleRetrieve} style={{ padding: '5px 10px' }}>
          Retrieve
        </button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}
      {result && (
        <div>
          {result.success ? (
            <p>Item {itemId} retrieved successfully!</p>
          ) : (
            <p>Retrieval failed</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Retrieve;