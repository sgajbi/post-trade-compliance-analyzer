import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [uploadResponse, setUploadResponse] = useState(null);
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // --- NEW State for Product Shelf ---
  const [productShelfData, setProductShelfData] = useState([]);


  // --- Existing Handlers for File Upload ---
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setErrorMessage(""); // Clear any previous errors
    setUploadResponse(null); // Clear previous response
  };

  const handleUpload = async () => {
    if (!file) {
      setErrorMessage("Please select a file to upload.");
      return;
    }
    setLoading(true);
    setErrorMessage("");
    setUploadResponse(null);

    const formData = new FormData();
    formData.append("file", file); // Backend expects "file" as the field name

    try {
      const response = await axios.post("http://localhost:8000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setUploadResponse(response.data);
      setErrorMessage("");
    } catch (err) {
      console.error("Error uploading portfolio:", err);
      if (err.response) {
        setErrorMessage(`Upload failed: ${err.response.data.detail || err.message}`);
      } else {
        setErrorMessage(`Upload failed: ${err.message}`);
      }
      setUploadResponse(null);
    } finally {
      setLoading(false);
    }
  };

  // --- NEW Handler for Fetching Product Shelf ---
  const fetchProductShelf = async () => {
    setLoading(true);
    setErrorMessage("");
    try {
      const response = await axios.get("http://localhost:8000/product-shelf");
      setProductShelfData(response.data);
      setErrorMessage("");
    } catch (err) {
      console.error("Error fetching product shelf:", err);
      if (err.response) {
        setErrorMessage(`Failed to load product shelf: ${err.response.data.detail || err.message}`);
      } else {
        setErrorMessage(`Failed to load product shelf: ${err.message}`);
      }
      setProductShelfData([]);
    } finally {
      setLoading(false);
    }
  };


  // --- Existing Handlers for Chat ---
  const handleChatSubmit = async () => {
    const targetPortfolioId = uploadResponse?.portfolio_id; // Only considers uploaded portfolio for now
    if (!targetPortfolioId || !chatQuestion) {
      setErrorMessage("Please upload a portfolio first and enter a question.");
      return;
    }
    setLoading(true);
    setErrorMessage("");
    setChatAnswer("");

    try {
      const response = await axios.post(
        `http://localhost:8000/ask/${targetPortfolioId}`,
        null, // No request body
        {
          params: {
            question: chatQuestion,
          },
        }
      );
      setChatAnswer(response.data.answer);
    } catch (err) {
      console.error("Error asking question:", err);
      setChatAnswer("❌ Failed to get response from server.");
      if (err.response) {
        setErrorMessage(`Chat failed: ${err.response.data.detail || err.message}`);
      } else {
        setErrorMessage(`Chat failed: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="app-container">
      <h1>📊 Post-Trade Compliance Analyzer</h1>

      {loading && <p className="loading-message">Loading... Please wait.</p>}
      {errorMessage && <p className="error-message">🚨 {errorMessage}</p>}

      {/* --- Existing Upload Section --- */}
      <div className="upload-section">
        <h3>📤 Upload Existing Portfolio:</h3>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={loading}>
          Upload Portfolio
        </button>
      </div>

      {file && (
        <div className="preview-box">
          <h3>📋 Preview of Uploaded File:</h3>
          <p>
            <strong>Filename:</strong> {file.name}
          </p>
        </div>
      )}

      {uploadResponse && (
        <div className="result-section">
          <h3>🚨 Policy Violations:</h3>
          <ul>
            {uploadResponse.analysis.policy_violations.length === 0 ? (
              <li>✅ None</li>
            ) : (
              uploadResponse.analysis.policy_violations.map((item, i) => (
                <li key={i}>{item}</li>
              ))
            )}
          </ul>

          <h3>📉 Risk Drift Alerts:</h3>
          <ul>
            {uploadResponse.analysis.risk_drifts.length === 0 ? (
              <li>✅ None</li>
            ) : (
              uploadResponse.analysis.risk_drifts.map((item, i) => (
                <li key={i}>{item}</li>
              ))
            )}
          </ul>
        </div>
      )}

      <hr style={{ margin: "40px 0", borderTop: "1px dashed var(--medium-gray)" }} />

      {/* --- NEW Product Shelf Section --- */}
      <div className="product-shelf-section">
        <h3>🛍️ Product Shelf: Available Instruments</h3>
        <button onClick={fetchProductShelf} disabled={loading}>
          Load Product Shelf
        </button>

        {productShelfData.length > 0 && (
          <div className="product-list">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Name</th>
                  <th>Sector</th>
                  <th>Price ({productShelfData[0].currency})</th>
                  <th>ISIN</th>
                </tr>
              </thead>
              <tbody>
                {productShelfData.map((product, index) => (
                  <tr key={index}>
                    <td>{product.symbol}</td>
                    <td>{product.name}</td>
                    <td>{product.sector}</td>
                    <td>{product.market_price.toFixed(2)}</td>
                    <td>{product.isin}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {productShelfData.length === 0 && !loading && !errorMessage && (
            <p>Click "Load Product Shelf" to see available instruments.</p>
        )}
      </div>

      <hr style={{ margin: "40px 0", borderTop: "1px dashed var(--medium-gray)" }} />

      {/* --- Existing Chat Section --- */}
      <div className="chat-section">
        <h3>💬 Ask Compliance Questions:</h3>
        <input
          type="text"
          value={chatQuestion}
          onChange={(e) => setChatQuestion(e.target.value)}
          placeholder="e.g., Was there any risk drift in the portfolio?"
          disabled={loading || !uploadResponse}
        />
        <button onClick={handleChatSubmit} disabled={loading || !uploadResponse}>
          Ask
        </button>
        {chatAnswer && <p className="chat-answer">🤖 {chatAnswer}</p>}
      </div>
    </div>
  );
}

export default App;