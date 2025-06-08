import { useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/')
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => console.error('API error:', err));
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-2">Post-Trade Compliance Analyzer</h1>
      <p>Backend says: <strong>{message}</strong></p>
    </div>
  );
}

export default App;
