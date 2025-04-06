import React from 'react';
import Search from './components/Search';
import Retrieve from './components/Retrieve';

function App() {
  return (
    <div style={{ fontFamily: 'Arial', padding: '20px' }}>
      <h1>Cargo Stowage Management System</h1>
      <Search />
      <Retrieve />
    </div>
  );
}

export default App;