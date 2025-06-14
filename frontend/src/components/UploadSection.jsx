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
    setUploadResponse(null); // Clear previous analysis results *at the start* of a new upload attempt

    try {
      console.log('handleUpload: Calling uploadPortfolio API...'); // DEBUG
      const responseData = await api.uploadPortfolio(file);
      console.log('handleUpload: API success. Response data received:', responseData); // DEBUG
      setUploadResponse(responseData); // Update the parent's uploadResponse state
    } catch (error) {
      console.error('handleUpload: API Error uploading portfolio:', error); // DEBUG
      const msg = error.response?.data?.detail || 'Failed to upload portfolio.';
      setLocalErrorMessage(msg); // Show error locally within this component
      setUploadResponse(null); // Ensure parent's response is null on current upload failure
    } finally {
      setUploading(false); // End loading indicator
      console.log('handleUpload: Upload process finished. Current uploadResponse (after state update):', uploadResponse); // DEBUG
    }
  };

  return (
    <div className="upload-section">
      <h3>📁 Upload Portfolio</h3>
      <input type="file" onChange={handleFileChange} />
      {/* Disable button while uploading */}
      <button onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Uploading...' : 'Upload Portfolio'}
      </button>

      {/* Display local error messages */}
      {localErrorMessage && <p className="error-message" style={{ color: 'red' }}>{localErrorMessage}</p>}

      {/* Display temporary preview of selected file if no analysis is present and no local error */}
      {file && !uploadResponse && !localErrorMessage && (
        <div className="preview-box">
          <h3>📋 Selected File:</h3>
          <p><strong>Filename:</strong> {file.name}</p>
        </div>
      )}

      {/* Display actual analysis result from uploadResponse, with defensive checks */}
      {uploadResponse && uploadResponse.analysis && (
        <div className="result-section">
          <h3>📋 Analysis for: {uploadResponse.filename || 'Unknown File'}</h3> {/* Fallback for filename */}
          <h4>Policy Violations:</h4>
          <ul>
            {uploadResponse.analysis.policy_violations && uploadResponse.analysis.policy_violations.length === 0 ? (
              <li>✅ None</li>
            ) : (
              // Ensure policy_violations is an array before mapping
              Array.isArray(uploadResponse.analysis.policy_violations) && uploadResponse.analysis.policy_violations.map((item, i) => <li key={i}>{item}</li>)
            )}
          </ul>

          <h4>Risk Drift Alerts:</h4>
          <ul>
            {uploadResponse.analysis.risk_drifts && uploadResponse.analysis.risk_drifts.length === 0 ? (
              <li>✅ None</li>
            ) : (
              // Ensure risk_drifts is an array before mapping
              Array.isArray(uploadResponse.analysis.risk_drifts) && uploadResponse.analysis.risk_drifts.map((item, i) => (
                <li key={i}>
                  Risk drift in {item.sector}: Actual {item.actual}, Model {item.model}
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