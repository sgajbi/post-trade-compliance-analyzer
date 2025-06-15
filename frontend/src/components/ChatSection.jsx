import React from 'react'; // Removed useState as state is lifted
import api from '../services/api'; // api is still needed here for the actual fetch

const ChatSection = ({
  uploadResponse,
  setAppErrorMessage,
  chatQuestion,
  setChatQuestion,
  chatAnswer,
  setChatAnswer,
  loadingChat,
  setLoadingChat,
  handleChatSubmit // Receive the handler from App.jsx
}) => {
  // Removed internal state for chatQuestion, chatAnswer, loadingChat and handleChatSubmit

  return (
    <div className="chat-section">
      <h3>🤖 Ask Compliance Questions:</h3>
      <input
        type="text"
        value={chatQuestion}
        onChange={(e) => setChatQuestion(e.target.value)} // Use setChatQuestion from props
        placeholder="e.g., Was there any risk drift in the portfolio?"
        disabled={loadingChat}
      />
      <button onClick={handleChatSubmit} disabled={loadingChat}>
        {loadingChat ? 'Asking...' : 'Ask'}
      </button>
      {chatAnswer && <p className="chat-answer">💬 {chatAnswer}</p>}
    </div>
  );
};

export default ChatSection;