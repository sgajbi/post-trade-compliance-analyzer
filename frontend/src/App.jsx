import { useState } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const [preview, setPreview] = useState('');

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      setPreview(data.preview);
      setPreview(
        `Policy Violations:\n${data.analysis.policy_violations.join('\n') || 'None'}\n\n` +
        `Risk Drift Alerts:\n${data.analysis.risk_drifts.join('\n') || 'None'}`
      );
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-2">Post-Trade Compliance Analyzer</h1>

      <input type="file" onChange={handleFileUpload} className="mb-4" />

      {preview && (
        <div className="bg-gray-100 p-2 rounded border">
          <h2 className="font-semibold">📋 Preview of Uploaded File:</h2>
          <pre className="text-sm whitespace-pre-wrap">{preview}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
