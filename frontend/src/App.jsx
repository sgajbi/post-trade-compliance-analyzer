
import React, { useState, useEffect } from 'react';
import './App.css';
import UploadSection from './components/UploadSection';
import api from './services/api'; // Ensure api is imported for the chat section and new data fetches

function App() {
  const [uploadResponse, setUploadResponse] = useState(null);
  const [chatQuestion, setChatQuestion] = useState('');
  const [chatAnswer, setChatAnswer] = useState('');
  const [errorMessage, setErrorMessage] = useState(''); // Global error message state
  const [clients, setClients] = useState([]); // New state for clients
  const [productShelf, setProductShelf] = useState([]); // New state for product shelf
  const [loadingClients, setLoadingClients] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(false);


  // --- DEBUGGING LOGS ---
  console.log('App.jsx render: global uploadResponse:', uploadResponse);
  console.log('App.jsx render: global errorMessage:', errorMessage);
  // --- END DEBUGGING LOGS ---

  // Fetch clients and product shelf data on component mount
  useEffect(() => {
    const fetchStaticData = async () => {
      setLoadingClients(true);
      setLoadingProducts(true);
      try {
        const clientsData = await api.fetchClients();
        setClients(clientsData);
        console.log("Fetched Clients:", clientsData);

        const productShelfData = await api.fetchProductShelf();
        setProductShelf(productShelfData);
        console.log("Fetched Product Shelf:", productShelfData);
      } catch (err) {
        console.error("Error fetching static data:", err);
        setErrorMessage(`Failed to load static data: ${err.message || 'Network error'}`);
      } finally {
        setLoadingClients(false);
        setLoadingProducts(false);
      }
    };

    fetchStaticData();
  }, []); // Empty dependency array means this runs once on mount


  return (
    <div className="app-container">
      <h1>📊 Post-Trade Compliance Analyzer</h1>

      {/* Global error message display */}
      {errorMessage && <p className="error-message" style={{ color: 'red' }}>{errorMessage}</p>}

      {/* Pass setErrorMessage as setAppErrorMessage to differentiate */}
      <UploadSection
        uploadResponse={uploadResponse}
        setUploadResponse={setUploadResponse}
        setAppErrorMessage={setErrorMessage}
      />

      {/* The chat section remains */}
      <div className="chat-section">
        <h3>🤖 Ask Compliance Questions:</h3>
        <input
          type="text"
          value={chatQuestion}
          onChange={(e) => setChatQuestion(e.target.value)}
          placeholder="e.g., Was there any risk drift in the portfolio?"
        />
        <button
          onClick={async () => {
            console.log('Chat button clicked. Current uploadResponse for chat:', uploadResponse); // DEBUG
            if (!uploadResponse || !uploadResponse.portfolio_id) {
              setErrorMessage('Please upload a portfolio first to enable chat.');
              return;
            }
            if (!chatQuestion.trim()) {
              setErrorMessage('Please enter a question.');
              return;
            }
            setErrorMessage(''); // Clear previous global error
            try {
              const response = await api.askComplianceQuestion(uploadResponse.portfolio_id, chatQuestion);
              console.log('Chat API success. Response:', response); // DEBUG
              setChatAnswer(response.answer);
            } catch (err) {
              console.error('Chat API Error:', err); // DEBUG
              setErrorMessage(err.response?.data?.detail || 'Failed to get response from server.');
              setChatAnswer('❌ Failed to get response from server.');
            }
          }}
        >
          Ask
        </button>
        {chatAnswer && <p className="chat-answer">💬 {chatAnswer}</p>}
      </div>

      {/* Static Data Sections - New Addition */}
      <div className="static-data-section">
        <h2>Global Data</h2>

        {/* Clients Section */}
        <div className="clients-section">
          <h3>👥 Clients:</h3>
          {loadingClients ? (
            <p>Loading clients...</p>
          ) : clients.length === 0 ? (
            <p>No clients data available.</p>
          ) : (
            <ul>
              {clients.map((client) => (
                <li key={client.client_id}>
                  <strong>{client.name}</strong> ({client.client_id}) - Portfolios:{" "}
                  {client.portfolios.length}
                  <ul>
                    {client.portfolios.map((portfolio) => (
                      <li key={portfolio.portfolio_id}>
                        {portfolio.name} ({portfolio.portfolio_id}) - Risk:{" "}
                        {portfolio.risk_profile}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Product Shelf Section */}
        <div className="product-shelf-section">
          <h3>📦 Product Shelf:</h3>
          {loadingProducts ? (
            <p>Loading products...</p>
          ) : productShelf.length === 0 ? (
            <p>No product shelf data available.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Name</th>
                  <th>Sector</th>
                  <th>Price</th>
                </tr>
              </thead>
              <tbody>
                {productShelf.map((product) => (
                  <tr key={product.isin}>
                    <td>{product.symbol}</td>
                    <td>{product.name}</td>
                    <td>{product.sector}</td>
                    <td>{product.market_price} {product.currency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div> {/* End of static-data-section */}
    </div>
  );
}

export default App;