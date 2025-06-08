import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [uploadResponse, setUploadResponse] = useState(null);
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");
  const [isLoadingUpload, setIsLoadingUpload] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [chatError, setChatError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadResponse(null); // Clear previous response on new file selection
    setUploadError(null); // Clear previous errors
    setChatAnswer(""); // Clear previous chat answer
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadError("Please select a file to upload.");
      return;
    }

    setIsLoadingUpload(true);
    setUploadError(null); // Clear previous error
    setUploadResponse(null); // Clear previous response

    const formData = new FormData();
    formData.append("file", file); // Corrected key to "file" to match FastAPI endpoint

    try {
      const response = await axios.post("http://localhost:8000/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data", // Ensure correct content type for file uploads
        },
      });
      setUploadResponse(response.data);
      console.log("Upload successful:", response.data);
    } catch (error) {
      console.error("Error uploading portfolio:", error);
      const errorMessage = error.response
        ? error.response.data.detail || error.response.data.message || "Server error"
        : error.message || "Network error";
      setUploadError(`Failed to upload portfolio: ${errorMessage}`);
    } finally {
      setIsLoadingUpload(false);
    }
  };

  const handleChatSubmit = async () => {
    if (!uploadResponse || !uploadResponse.portfolio_id) {
      setChatError("Please upload a portfolio first.");
      return;
    }
    if (!chatQuestion.trim()) {
      setChatError("Please enter a question.");
      return;
    }

    setIsLoadingChat(true);
    setChatError(null); // Clear previous error
    setChatAnswer(""); // Clear previous answer

    try {
      const response = await axios.post(
        `http://localhost:8000/ask/${uploadResponse.portfolio_id}`,
        null, // No body needed for GET-like parameters
        {
          params: {
            question: chatQuestion,
          },
        }
      );
      setChatAnswer(response.data.answer);
    } catch (err) {
      console.error("Error asking question:", err);
      const errorMessage = err.response
        ? err.response.data.detail || err.response.data.message || "Server error"
        : err.message || "Network error";
      setChatAnswer("❌ Failed to get response from server.");
      setChatError(`Error: ${errorMessage}`);
    } finally {
      setIsLoadingChat(false);
    }
  };

  return (
    <div className="app-container">
      <h1>Post-Trade Compliance Analyzer</h1> {/* Icon added via CSS to h1 */}

      <div className="upload-section">
        <h3 className="upload-title">Upload Portfolio</h3> {/* Added class for icon */}
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={isLoadingUpload}>
          {isLoadingUpload ? "Uploading..." : "Upload Portfolio"}
        </button>
      </div>

      {uploadError && <p className="error-message">{uploadError}</p>}
      {isLoadingUpload && <p className="loading-message">Analyzing portfolio...</p>}

      {file && (
        <div className="preview-box">
          <h3 className="preview-title">Preview of Uploaded File:</h3> {/* Added class for icon */}
          <p>
            <strong>Filename:</strong> {file.name}
          </p>
        </div>
      )}

      {uploadResponse && uploadResponse.analysis && ( // Ensure analysis object exists
        <div className="result-section">
          <h3 className="violations-title">Policy Violations:</h3> {/* Added class for icon */}
          <ul>
            {uploadResponse.analysis.raw_policy_violations && uploadResponse.analysis.raw_policy_violations.length === 0 ? (
              <li className="success">✅ None</li>
            ) : (
              // Use raw_policy_violations as it's the list of strings
              uploadResponse.analysis.raw_policy_violations.map((item, i) => <li key={i}>{item}</li>)
            )}
          </ul>

          <h3 className="drifts-title">Risk Drift Alerts:</h3> {/* Added class for icon */}
          <ul>
            {uploadResponse.analysis.raw_risk_drifts && uploadResponse.analysis.raw_risk_drifts.length === 0 ? (
              <li className="success">✅ None</li>
            ) : (
              // Use raw_risk_drifts as it's the list of strings
              uploadResponse.analysis.raw_risk_drifts.map((item, i) => <li key={i}>{item}</li>)
            )}
          </ul>
        </div>
      )}

      <div className="chat-section">
        <h3 className="chat-title">Ask Compliance Questions:</h3> {/* Added class for icon */}
        <input
          type="text"
          value={chatQuestion}
          onChange={(e) => setChatQuestion(e.target.value)}
          placeholder="e.g., Was there any risk drift in the portfolio?"
          disabled={isLoadingChat}
        />
        <button onClick={handleChatSubmit} disabled={isLoadingChat || !uploadResponse || !uploadResponse.portfolio_id}>
          {isLoadingChat ? "Asking..." : "Ask"}
        </button>
        {chatError && <p className="error-message">{chatError}</p>}
        {isLoadingChat && <p className="loading-message">Thinking...</p>}
        {chatAnswer && <p className="chat-answer">💬 {chatAnswer}</p>}
      </div>
    </div>
  );
}

export default App;