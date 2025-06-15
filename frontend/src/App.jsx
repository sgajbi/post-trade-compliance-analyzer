import React, { useState, useEffect } from 'react';
import './App.css';
import UploadSection from './components/UploadSection';
import ProductShelfSection from './components/ProductShelfSection';
import ClientSection from './components/ClientSection';
import ChatSection from './components/ChatSection';
import api from './services/api';

function App() {
  const [uploadResponse, setUploadResponse] = useState(null);
  const [errorMessage, setErrorMessage] = useState(''); // Global error message state
  const [activeTab, setActiveTab] = useState('upload'); // State to manage active tab

  // --- State for Product Shelf ---
  const [products, setProducts] = useState(null);
  const [loadingProducts, setLoadingProducts] = useState(false);

  // --- State for Clients ---
  const [clients, setClients] = useState(null);
  const [loadingClients, setLoadingClients] = useState(false);

  // --- State for Chat ---
  const [chatQuestion, setChatQuestion] = useState('');
  const [chatAnswer, setChatAnswer] = useState('');
  const [loadingChat, setLoadingChat] = useState(false);

  // --- Fetch Functions (lifted from components) ---

  const fetchProducts = async () => {
    setLoadingProducts(true);
    setErrorMessage(''); // Clear any global error
    try {
      const data = await api.fetchProductShelf();
      setProducts(data);
      console.log('Product Shelf Data:', data); // Debugging
    } catch (error) {
      console.error('Error fetching product shelf:', error);
      const msg = error.response?.data?.detail || 'Failed to fetch product shelf data.';
      setErrorMessage(msg); // Set global error
      setProducts(null); // Clear products on error
    } finally {
      setLoadingProducts(false);
    }
  };

  const fetchClients = async () => {
    setLoadingClients(true);
    setErrorMessage(''); // Clear any global error
    try {
      const data = await api.fetchClients();
      setClients(data);
      console.log('Clients Data:', data); // Debugging
    } catch (error) {
      console.error('Error fetching clients:', error);
      const msg = error.response?.data?.detail || 'Failed to fetch clients data.';
      setErrorMessage(msg); // Set global error
      setClients(null); // Clear clients on error
    } finally {
      setLoadingClients(false);
    }
  };

  const handleChatSubmit = async () => {
    console.log('Chat button clicked. Current uploadResponse for chat:', uploadResponse); // DEBUG
    if (!uploadResponse || !uploadResponse.portfolio_id) {
      setErrorMessage('Please upload a portfolio first to enable chat.');
      return;
    }
    if (!chatQuestion.trim()) {
      setErrorMessage('Please enter a question.');
      return;
    }

    setLoadingChat(true);
    setErrorMessage(''); // Clear previous global error
    setChatAnswer(''); // Clear previous answer

    try {
      const response = await api.askComplianceQuestion(uploadResponse.portfolio_id, chatQuestion);
      console.log('Chat API success. Response:', response); // DEBUG
      setChatAnswer(response.answer);
    } catch (err) {
      console.error('Chat API Error:', err); // DEBUG
      setErrorMessage(err.response?.data?.detail || 'Failed to get response from server.');
      setChatAnswer('❌ Failed to get response from server.');
    } finally {
      setLoadingChat(false);
    }
  };


  // --- useEffect for initial data fetches based on active tab ---
  // This ensures data is loaded only when that tab is first visited,
  // or when the component mounts if 'upload' is the default.
  useEffect(() => {
    // Fetch product shelf data if the tab is active and data hasn't been loaded yet
    if (activeTab === 'productShelf' && products === null && !loadingProducts) {
      fetchProducts();
    }
    // Fetch clients data if the tab is active and data hasn't been loaded yet
    if (activeTab === 'clients' && clients === null && !loadingClients) {
      fetchClients();
    }
  }, [activeTab]); // Re-run effect when activeTab changes

  // --- DEBUGGING LOGS ---
  console.log('App.jsx render: global uploadResponse:', uploadResponse);
  console.log('App.jsx render: global errorMessage:', errorMessage);
  // --- END DEBUGGING LOGS ---

  return (
    <div className="app-container">
      <h1>📊 Post-Trade Compliance Analyzer</h1>

      {/* Global error message display */}
      {errorMessage && <p className="error-message" style={{ color: 'red' }}>{errorMessage}</p>}

      {/* Tab Navigation */}
      <div className="tabs">
        <button
          className={activeTab === 'upload' ? 'active' : ''}
          onClick={() => setActiveTab('upload')}
        >
          Upload Portfolio
        </button>
        <button
          className={activeTab === 'productShelf' ? 'active' : ''}
          onClick={() => setActiveTab('productShelf')}
        >
          Product Shelf
        </button>
        <button
          className={activeTab === 'clients' ? 'active' : ''}
          onClick={() => setActiveTab('clients')}
        >
          Our Clients
        </button>
        <button
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          Compliance Chat
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'upload' && (
          <UploadSection
            uploadResponse={uploadResponse}
            setUploadResponse={setUploadResponse}
            setAppErrorMessage={setErrorMessage}
          />
        )}

        {activeTab === 'productShelf' && (
          <ProductShelfSection
            products={products}
            loadingProducts={loadingProducts}
            fetchProducts={fetchProducts} // Pass the fetch function
            setAppErrorMessage={setErrorMessage}
          />
        )}

        {activeTab === 'clients' && (
          <ClientSection
            clients={clients}
            loadingClients={loadingClients}
            fetchClients={fetchClients} // Pass the fetch function
            setAppErrorMessage={setErrorMessage}
          />
        )}

        {activeTab === 'chat' && (
          <ChatSection
            uploadResponse={uploadResponse}
            setAppErrorMessage={setErrorMessage}
            chatQuestion={chatQuestion}
            setChatQuestion={setChatQuestion}
            chatAnswer={chatAnswer}
            setChatAnswer={setChatAnswer}
            loadingChat={loadingChat}
            setLoadingChat={setLoadingChat}
            handleChatSubmit={handleChatSubmit} // Pass the submit handler
          />
        )}
      </div>
    </div>
  );
}

export default App;