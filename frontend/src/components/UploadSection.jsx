// frontend/src/components/UploadSection.jsx
import React, { useState } from 'react';
import api from '../services/api';

const UploadSection = ({ uploadResponse, setUploadResponse, setAppErrorMessage }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [localErrorMessage, setLocalErrorMessage] = useState('');

  // --- DEBUGGING LOGS ---
  console.log('UploadSection render: uploadResponse prop:', uploadResponse);
  console.log('UploadSection render: file state:', file);
  console.log('UploadSection render: localErrorMessage:', localErrorMessage);
  // --- END DEBUGGING LOGS ---


  const handleFileChange = (e) => {
    console.log('handleFileChange: New file selected.'); // DEBUG
    setFile(e.target.files[0]);
    setLocalErrorMessage(''); // Clear any local error when a new file is selected
    setAppErrorMessage(''); // Clear any global error as well
    // We do NOT clear uploadResponse here. Previous analysis should remain until a new upload completes/fails.
  };

  const handleUpload = async () => {
    console.log('handleUpload: Initiating upload...'); // DEBUG
    if (!file) {
      setLocalErrorMessage('Please select a file to upload.');
      setAppErrorMessage('');
      console.log('handleUpload: No file selected. Aborting.'); // DEBUG
      return;
    }

    setUploading(true); // Start loading indicator
    setLocalErrorMessage(''); // Clear previous local error
    setAppErrorMessage(''); // Clear previous global error

    try {
      const response = await api.uploadPortfolio(file);
      console.log('Upload API success. Response:', response); // DEBUG

      // Correctly access nested analysis data and update state
      setUploadResponse({
        filename: response.filename,
        portfolio_id: response.portfolio_id,
        status: response.status,
        analysis: { // Ensure analysis object exists
          policy_violations: response.analysis?.raw_policy_violations || [],
          risk_drifts: response.analysis?.raw_risk_drifts || [],
        }
      });
      console.log('Upload successful. UploadResponse updated:', response); // DEBUG

    } catch (err) {
      console.error('Upload API Error:', err); // DEBUG
      const errorMsg = err.response?.data?.detail || err.message || 'An unknown error occurred during upload.';
      setLocalErrorMessage(`Upload failed: ${errorMsg}`);
      setAppErrorMessage(`Upload failed: ${errorMsg}`); // Also set global error
      setUploadResponse(null); // Clear response on error
    } finally {
      setUploading(false); // End loading indicator
    }
  };

  return (
    <div className="upload-section">
      <h2>Upload Portfolio</h2>
      <div className="upload-controls">
        <input type="file" onChange={handleFileChange} accept=".json" />
        <button onClick={handleUpload} disabled={uploading}>
          {uploading ? 'Uploading...' : 'Upload Portfolio'}
        </button>
      </div>

      {localErrorMessage && <p className="error-message">{localErrorMessage}</p>}

      {file && (
        <div className="preview-box">
          <h3>📋 Preview of Uploaded File:</h3>
          <p><strong>Filename:</strong> {file.name}</p>
        </div>
      )}

      {/* Display actual analysis result from uploadResponse, with defensive checks */}
      {uploadResponse && uploadResponse.analysis && (
        <div className="result-section">
          <h3>📋 Analysis for: {uploadResponse.filename || 'Unknown File'}</h3>
          <h4>Policy Violations:</h4>
          <ul>
            {/* Ensure policy_violations is an array before mapping */}
            {Array.isArray(uploadResponse.analysis.policy_violations) && uploadResponse.analysis.policy_violations.length === 0 ? (
              <li className="green">✅ None</li>
            ) : (
              Array.isArray(uploadResponse.analysis.policy_violations) && uploadResponse.analysis.policy_violations.map((item, i) => <li key={i}>{item}</li>)
            )}
          </ul>

          <h4>Risk Drift Alerts:</h4>
          <ul>
            {/* Ensure risk_drifts is an array before mapping */}
            {Array.isArray(uploadResponse.analysis.risk_drifts) && uploadResponse.analysis.risk_drifts.length === 0 ? (
              <li className="green">✅ None</li>
            ) : (
              Array.isArray(uploadResponse.analysis.risk_drifts) && uploadResponse.analysis.risk_drifts.map((item, i) => (
                <li key={i}>
                  Risk drift in {item.sector}: Actual {item.actual.toFixed(2)}, Model {item.model.toFixed(2)}, Drift {item.drift.toFixed(2)} (Threshold: {item.threshold.toFixed(2)})
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

export default UploadSection;