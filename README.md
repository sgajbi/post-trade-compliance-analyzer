# 📊 Post-Trade Compliance Analyzer

This project provides a robust solution for analyzing investment portfolios against predefined compliance policies and identifying risk drifts. It features a user-friendly web interface for uploading portfolio data and an AI-powered chat assistant to answer compliance-related questions.

## ✨ Features

- **Portfolio Upload:** Easily upload JSON files containing portfolio positions and trades.
- **Compliance Validation:** Automatically checks uploaded portfolios against defined policy rules (e.g., sector-specific quantity limits).
- **Risk Drift Analysis:** Identifies deviations from target model allocations for different sectors within the portfolio.
- **Detailed Reporting:** Generates a comprehensive report detailing policy violations and risk drift alerts.
- **AI-Powered Compliance Q&A:** Ask natural language questions about the uploaded portfolio's compliance status and receive intelligent answers based on the analysis report.
- **Modern UI:** A clean, organized, and professional user interface for seamless interaction.

## 🏗️ Architecture

The application is structured into a frontend and a backend, leveraging various agents and services for its functionality:

- **Frontend (React.js):**

  - Built with React, managing user interactions, file uploads, and displaying compliance results and chat responses.
  - Communicates with the FastAPI backend via `axios`.
  - Styled using a custom CSS file (`App.css`) for a professional look.
  - Located in the `frontend/` directory.

- **Backend (FastAPI):**

  - A Python FastAPI application serving as the API for the frontend.
  - Handles file uploads, orchestrates the analysis agents, stores data, and manages the RAG service.
  - Includes CORS middleware for cross-origin requests.
  - Located in the `backend/` directory.

- **Compliance Agents:**

  - `PolicyValidatorAgent`: Checks portfolio positions against predefined compliance rules.
  - `RiskDriftAgent`: Calculates actual sector weights and identifies drifts from model allocations.
  - `BreachReporterAgent`: Consolidates findings from policy validation and risk drift analysis into a comprehensive report.
  - These agents are located in the `backend/agents/` directory.

- **Database (MongoDB):**

  - Used for persistently storing uploaded portfolio details and their analysis reports, managed via `mongo.py`.

- **RAG Service (ChromaDB + SentenceTransformer + OpenAI):**
  - `rag_service.py`: Implements a Retrieval-Augmented Generation (RAG) system.
  - **ChromaDB:** A vector database for storing embedded sections of the portfolio analysis reports.
  - **SentenceTransformer:** Used to generate embeddings for the text content.
  - **OpenAI GPT-4:** Leveraged as the large language model (LLM) to generate answers based on the retrieved context from ChromaDB.

## ⚙️ Setup and Installation

Follow these steps to get the project up and running locally.

### Prerequisites

- Python 3.9+
- Node.js and npm (or yarn)
- MongoDB (running locally or accessible via a connection string)
- An OpenAI API Key

### 1. Clone the Repository

```bash
git clone [https://github.com/sgajbi/post-trade-compliance-analyzer.git](https://github.com/sgajbi/post-trade-compliance-analyzer.git)
cd post-trade-compliance-analyzer
```

### 2. Backend Setup

1.  **Navigate to the backend directory:**

    ```bash
    cd backend
    ```

2.  **Create a virtual environment and activate it:**

    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    # Alternatively, if requirements.txt is not provided, use:
    # pip install fastapi uvicorn python-multipart motor chromadb sentence-transformers openai python-dotenv
    ```

4.  **Set up Environment Variables:**
    Create a `.env` file in the `backend/` directory (where `main.py` is located) and add your OpenAI API key:

    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    ```

5.  **Run the Backend:**

    ```bash
    uvicorn main:app --reload
    ```

    The backend will run on `http://localhost:8000`.

### 3. Frontend Setup

1.  **Navigate to the frontend directory:**
    (First go back to the root of the project if you are in `backend`)

    ```bash
    cd ..
    cd frontend
    ```

2.  **Install Node.js dependencies:**

    ```bash
    npm install
    # or
    yarn install
    ```

3.  **Run the Frontend:**

    ```bash
    npm start
    # or
    yarn start
    ```

    This will usually open the application in your browser at `http://localhost:3000` (or another available port).

## 🚀 Usage

1.  **Start Backend and Frontend:** Ensure both the backend (FastAPI) and frontend (React) servers are running.
2.  **Upload Portfolio:** In the web interface, click "Choose File" and select a JSON file (e.g., `sample_portfolio.json` from the project root) containing your portfolio data. Click "Upload Portfolio".
3.  **View Analysis:** The UI will display "Policy Violations" and "Risk Drift Alerts" based on the uploaded portfolio's analysis.
4.  **Ask Questions:** In the "Ask Compliance Questions" section, type your query related to the portfolio's compliance (e.g., "Was there any risk drift in the portfolio?" or "How is the portfolio doing?") and click "Ask". The AI assistant will provide an answer.

## 🤝 Contributing

Feel free to fork this repository and contribute! Please open an issue or submit a pull request for any improvements or bug fixes.
