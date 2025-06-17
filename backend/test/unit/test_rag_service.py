# backend/test/unit/test_rag_service.py
import pytest
from unittest.mock import MagicMock
from bson import ObjectId

# --- Mocking dependencies for rag_service tests ---
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

    # Import rag_service after setting up mocks
    # This also means we need to ensure rag_service's initialization is delayed or uses a callable for OpenAI/Chroma
    from rag_service import set_rag_components, get_rag_collection, get_embedding_function, get_chroma_client

    mock_client = MockChromaClient("test_path")
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