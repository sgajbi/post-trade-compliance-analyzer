import React, { useState } from 'react';
import './App.css';
import UploadSection from './components/UploadSection';
import api from './services/api'; // Ensure api is imported for the chat section

function App() {
  const [uploadResponse, setUploadResponse] = useState(null);
  const [chatQuestion, setChatQuestion] = useState('');
  const [chatAnswer, setChatAnswer] = useState('');
  const [errorMessage, setErrorMessage] = useState(''); // Global error message state

  // --- DEBUGGING LOGS ---
  console.log('App.jsx render: global uploadResponse:', uploadResponse);
  console.log('App.jsx render: global errorMessage:', errorMessage);
  // --- END DEBUGGING LOGS ---

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

      {/* The chat section remains for now */}
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
    </div>
  );
}

export default App;