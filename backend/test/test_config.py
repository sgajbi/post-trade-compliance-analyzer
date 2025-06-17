# backend/tests/test_config.py
import os
import pytest
from pydantic import ValidationError # Import ValidationError
from core.config import Settings
from unittest.mock import MagicMock # Import MagicMock for more flexible mocking

# Mocking dependencies for rag_service tests
class MockChromaClient:
    def __init__(self, path):
        self.path = path
    def get_or_create_collection(self, name, embedding_function):
        return MockCollection(name, embedding_function)

class MockCollection:
    def __init__(self, name, embedding_function):
        self.name = name
        self.embedding_function = embedding_function
        self.documents = []
        self.metadatas = []
        self.ids = []

    def add(self, documents, metadatas, ids):
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)
        # print(f"MockCollection: Added {len(documents)} documents. Total: {len(self.documents)}")

    def query(self, query_embeddings, n_results, where):
        # Simplistic mock query for testing purposes
        # In a real test, you'd likely mock based on expected inputs and outputs
        if "$and" in where and len(where["$and"]) == 2:
            client_id_cond = where["$and"][0]
            portfolio_id_cond = where["$and"][1]
            if "client_id" in client_id_cond and "portfolio_id" in portfolio_id_cond:
                if "TEST_CLIENT" == client_id_cond["client_id"] and "TEST_PORTFOLIO" == portfolio_id_cond["portfolio_id"]:
                    return {"documents": [["Test context for TEST_CLIENT/TEST_PORTFOLIO"]]}
        return {"documents": []} # Return empty if no match

# Re-import for type hinting in rag_service, but we won't instantiate it
# from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Corrected MockEmbeddingFunction: Does not inherit from SentenceTransformerEmbeddingFunction
# and does not call super().__init__ to avoid loading a real model.
class MockEmbeddingFunction:
    def __init__(self, model_name):
        self.model_name = model_name
    def __call__(self, texts):
        # Return dummy embeddings for any given text
        return [[float(i) * 0.1 for i in range(len(text))] for text in texts] # Return a list of lists of floats

class MockOpenAIClient:
    def __init__(self, api_key):
        self.api_key = api_key
    class Chat:
        class Completions:
            def create(self, model, messages):
                class MockChoice:
                    class MockMessage:
                        def __init__(self, content):
                            self.content = content
                        content: str
                    message: MockMessage
                    def __init__(self, content):
                        self.message = self.MockMessage(content)
                # Simulate a response based on messages
                # Check for "compliance assistant" to differentiate answers
                if any("compliance assistant" in m["content"] for m in messages):
                    return type('obj', (object,), {'choices': [MockChoice("Mocked compliance answer.")]})()
                return type('obj', (object,), {'choices': [MockChoice("Mocked general answer.")]})()
        completions = Completions()
    chat = Chat()

# Helper function to clear relevant environment variables for tests
def _clear_settings_env_vars(monkeypatch):
    monkeypatch.delenv("CHROMA_DB_PATH", raising=False)
    monkeypatch.delenv("CHROMA_COLLECTION_NAME", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL_NAME", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("APP_NAME", raising=False) # Clear APP_NAME if it's set in env

# --- Test Case 1: Test default settings loading (expecting ValidationError for missing required fields) ---
def test_default_settings_loading(monkeypatch, tmp_path):
    """
    Tests that a ValidationError is raised when required settings (like OPENAI_API_KEY) are not set
    and no .env file is present.
    """
    _clear_settings_env_vars(monkeypatch)
    # Change current working directory to a temporary path to ensure no real .env file is found
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError) as excinfo:
        Settings()
    assert "OPENAI_API_KEY" in str(excinfo.value) # Check that the error message relates to OPENAI_API_KEY


# --- Test Case 2: Test settings loading from environment variables ---
def test_env_var_settings_loading(monkeypatch):
    """
    Tests that settings are loaded correctly from environment variables.
    """
    _clear_settings_env_vars(monkeypatch) # Clear existing env vars first
    monkeypatch.setenv("CHROMA_DB_PATH", "/tmp/my_test_db")
    monkeypatch.setenv("CHROMA_COLLECTION_NAME", "test_collection")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key_123")
    monkeypatch.setenv("APP_NAME", "Test App From Env")
    monkeypatch.setenv("ENV", "test") # Set ENV for consistent behavior

    settings = Settings()
    assert settings.APP_NAME == "Test App From Env"
    assert settings.CHROMA_DB_PATH == "/tmp/my_test_db"
    assert settings.CHROMA_COLLECTION_NAME == "test_collection"
    assert settings.OPENAI_API_KEY == "test_openai_key_123"

# --- Test Case 3: Test .env file loading (requires creating a temp .env) ---
def test_dot_env_file_settings_loading(tmp_path, monkeypatch):
    """
    Tests that settings are loaded correctly from a .env file.
    Uses pytest's tmp_path fixture to create a temporary .env file.
    """
    _clear_settings_env_vars(monkeypatch) # Clear existing env vars first

    # Create a temporary .env file in the tmp_path
    env_content = """
CHROMA_DB_PATH=/path/from/env_file
CHROMA_COLLECTION_NAME=env_collection
OPENAI_API_KEY=env_openai_key_from_file
APP_NAME=Test App From DotEnv
    """
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)

    # Change current working directory to where the .env file is for Settings to find it
    monkeypatch.chdir(tmp_path)

    # Re-instantiate settings to pick up the new .env file
    settings = Settings()
    assert settings.APP_NAME == "Test App From DotEnv"
    assert settings.CHROMA_DB_PATH == "/path/from/env_file"
    assert settings.CHROMA_COLLECTION_NAME == "env_collection"
    assert settings.OPENAI_API_KEY == "env_openai_key_from_file"


# --- Test Case 4: Test required OpenAI API Key (explicitly checking for ValidationError) ---
def test_openai_api_key_missing_raises_error(monkeypatch, tmp_path):
    """
    Tests that a ValidationError is raised if OPENAI_API_KEY is not set.
    """
    _clear_settings_env_vars(monkeypatch) # Clear all env vars, including OPENAI_API_KEY
    # Change current working directory to a temporary path to ensure no real .env file is found
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError) as excinfo:
        Settings()
    # Check that the error message relates to OPENAI_API_KEY
    assert "OPENAI_API_KEY" in str(excinfo.value)

# --- Test Case 5: Test set_rag_components and get_rag_collection ---
@pytest.mark.asyncio
async def test_set_and_get_rag_components(monkeypatch):
    # Import locally to ensure changes in rag_service are picked up
    # We use MagicMock for embedding_functions.SentenceTransformerEmbeddingFunction
    # to avoid attempting to load a real model.
    mock_ef_class = MagicMock()
    mock_ef_instance = MockEmbeddingFunction(model_name="test_model_name")
    mock_ef_class.return_value = mock_ef_instance
    monkeypatch.setattr('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction', mock_ef_class)

    from rag_service import set_rag_components, get_rag_collection, get_embedding_function, get_chroma_client

    mock_client = MockChromaClient("test_path")
    # Use our MockEmbeddingFunction instance, not a type directly from chromadb
    mock_ef = mock_ef_instance
    mock_collection = MockCollection("test_name", mock_ef)

    set_rag_components(mock_client, mock_ef, mock_collection)

    assert get_chroma_client() is mock_client
    assert get_embedding_function() is mock_ef
    assert get_rag_collection() is mock_collection

    # Test error when not initialized
    monkeypatch.setattr('rag_service._chroma_client', None)
    with pytest.raises(RuntimeError, match="ChromaDB client not initialized"):
        get_chroma_client()

    monkeypatch.setattr('rag_service._embedding_function', None)
    with pytest.raises(RuntimeError, match="Embedding function not initialized"):
        get_embedding_function()

    monkeypatch.setattr('rag_service._rag_collection', None)
    with pytest.raises(RuntimeError, match="RAG collection not initialized"):
        get_rag_collection()

# --- Test Case 6: Test ingest_portfolio_analysis ---
@pytest.mark.asyncio
async def test_ingest_portfolio_analysis(monkeypatch):
    # Mock SentenceTransformerEmbeddingFunction for this test as well
    mock_ef_class = MagicMock()
    mock_ef_instance = MockEmbeddingFunction(model_name="test_model_name")
    mock_ef_class.return_value = mock_ef_instance
    monkeypatch.setattr('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction', mock_ef_class)

    from rag_service import ingest_portfolio_analysis, set_rag_components, get_rag_collection
    from bson import ObjectId # Ensure ObjectId is imported for the test data

    mock_client = MockChromaClient("test_path")
    mock_ef = mock_ef_instance
    mock_collection = MockCollection("test_name", mock_ef)
    set_rag_components(mock_client, mock_ef, mock_collection)

    portfolio_data = {
        "_id": ObjectId(),
        "compliance_report": "Some compliance details",
        "positions": ["pos1", "pos2"],
        "analysis": {"risk": "low"}
    }
    analysis_report = "Summary of analysis."

    await ingest_portfolio_analysis("test_client", portfolio_data, analysis_report, "test_portfolio")

    collection = get_rag_collection()
    assert len(collection.documents) == 1
    assert "Client ID: test_client" in collection.documents[0]
    assert "Portfolio ID: test_portfolio" in collection.documents[0]
    assert "Compliance Report Summary: Summary of analysis." in collection.documents[0]
    assert collection.metadatas[0]["client_id"] == "test_client"
    assert collection.metadatas[0]["portfolio_id"] == "test_portfolio"

# --- Test Case 7: Test query_portfolio with context ---
@pytest.mark.asyncio
async def test_query_portfolio_with_context(monkeypatch):
    # Mock SentenceTransformerEmbeddingFunction
    mock_ef_class = MagicMock()
    mock_ef_instance = MockEmbeddingFunction(model_name="test_model_name")
    mock_ef_class.return_value = mock_ef_instance
    monkeypatch.setattr('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction', mock_ef_class)

    from rag_service import query_portfolio, set_rag_components
    from core.config import settings

    # Set mock OpenAI API key in settings
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "mock_key")
    monkeypatch.setattr("rag_service.OpenAI", MockOpenAIClient) # Mock the OpenAI client

    mock_client = MockChromaClient("test_path")
    mock_ef = mock_ef_instance
    mock_collection = MockCollection("test_name", mock_ef)
    set_rag_components(mock_client, mock_ef, mock_collection)

    # Simulate ingested data for querying
    mock_collection.add(
        documents=["Test context for TEST_CLIENT/TEST_PORTFOLIO"],
        metadatas=[{"client_id": "TEST_CLIENT", "portfolio_id": "TEST_PORTFOLIO"}],
        ids=["doc1"]
    )

    question = "What is the compliance status?"
    answer = await query_portfolio("test_client", "test_portfolio", question)
    assert "Mocked compliance answer." in answer # Check for our mocked OpenAI response

# --- Test Case 8: Test query_portfolio without context, with chat history ---
@pytest.mark.asyncio
async def test_query_portfolio_no_context_with_history(monkeypatch):
    # Mock SentenceTransformerEmbeddingFunction
    mock_ef_class = MagicMock()
    mock_ef_instance = MockEmbeddingFunction(model_name="test_model_name")
    mock_ef_class.return_value = mock_ef_instance
    monkeypatch.setattr('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction', mock_ef_class)

    from rag_service import query_portfolio, set_rag_components
    from core.config import settings

    # Set mock OpenAI API key in settings
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "mock_key")
    monkeypatch.setattr("rag_service.OpenAI", MockOpenAIClient) # Mock the OpenAI client

    mock_client = MockChromaClient("test_path")
    mock_ef = mock_ef_instance
    # Don't add documents to mock_collection to simulate no context
    mock_collection = MockCollection("test_name", mock_ef)
    set_rag_components(mock_client, mock_ef, mock_collection)

    question = "How are you?"
    chat_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "I am fine, thank you."}
    ]
    answer = await query_portfolio("non_existent_client", "non_existent_portfolio", question, chat_history)
    assert "Mocked general answer." in answer

# --- Test Case 9: Test query_portfolio without context and no chat history ---
@pytest.mark.asyncio
async def test_query_portfolio_no_context_no_history(monkeypatch):
    # Mock SentenceTransformerEmbeddingFunction
    mock_ef_class = MagicMock()
    mock_ef_instance = MockEmbeddingFunction(model_name="test_model_name")
    mock_ef_class.return_value = mock_ef_instance
    monkeypatch.setattr('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction', mock_ef_class)

    from rag_service import query_portfolio, set_rag_components
    from core.config import settings

    # Set mock OpenAI API key in settings
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "mock_key")
    monkeypatch.setattr("rag_service.OpenAI", MockOpenAIClient) # Mock the OpenAI client

    mock_client = MockChromaClient("test_path")
    mock_ef = mock_ef_instance
    mock_collection = MockCollection("test_name", mock_ef)
    set_rag_components(mock_client, mock_ef, mock_collection)

    question = "What is my name?"
    answer = await query_portfolio("non_existent_client", "non_existent_portfolio", question, chat_history=[])
    assert answer == "No relevant information found for this portfolio and question."

# --- Test Case 10: Test OpenAI API key missing handling in query_portfolio ---
@pytest.mark.asyncio
async def test_openai_api_key_missing_in_query(monkeypatch):
    # Mock SentenceTransformerEmbeddingFunction
    mock_ef_class = MagicMock()
    mock_ef_instance = MockEmbeddingFunction(model_name="test_model_name")
    mock_ef_class.return_value = mock_ef_instance
    monkeypatch.setattr('chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction', mock_ef_class)

    from rag_service import query_portfolio, set_rag_components
    from core.config import settings
    from fastapi import HTTPException # Ensure HTTPException is imported if expected in test

    # Temporarily unset the OpenAI API key in settings
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "") # Set to empty string

    mock_client = MockChromaClient("test_path")
    mock_ef = mock_ef_instance
    mock_collection = MockCollection("test_name", mock_ef)
    set_rag_components(mock_client, mock_ef, mock_collection)

    with pytest.raises(Exception, match="OpenAI API key is not configured"):
        await query_portfolio("test_client", "test_portfolio", "Test question")