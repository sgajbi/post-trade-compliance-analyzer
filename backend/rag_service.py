# rag_service.py
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os
import logging
from bson import ObjectId
from chromadb.api import models
from datetime import datetime
from fastapi import HTTPException # Import HTTPException

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# These will be set by the application's startup event in main.py
_chroma_client = None
_embedding_function = None
_rag_collection = None

# Constants for ChromaDB path and collection name
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "portfolio_analysis"

def set_rag_components(client: chromadb.PersistentClient, ef: embedding_functions.SentenceTransformerEmbeddingFunction, collection: models.Collection):
    """Sets the global ChromaDB client, embedding function, and collection."""
    global _chroma_client, _embedding_function, _rag_collection
    _chroma_client = client
    _embedding_function = ef
    _rag_collection = collection
    logger.info("RAG components (ChromaDB client, embedding function, collection) have been set.")

def get_chroma_client():
    if _chroma_client is None:
        raise RuntimeError("ChromaDB client not initialized. Ensure app startup event ran.")
    return _chroma_client

def get_embedding_function():
    if _embedding_function is None:
        raise RuntimeError("Embedding function not initialized. Ensure app startup event ran.")
    return _embedding_function

def get_rag_collection():
    if _rag_collection is None:
        raise RuntimeError("RAG collection not initialized. Ensure app startup event ran.")
    return _rag_collection

async def ingest_portfolio_analysis(client_id: str, portfolio_data: dict, analysis_report: str, portfolio_id: str):
    """
    Ingests portfolio analysis and report into ChromaDB for RAG.
    Each portfolio document is ingested with metadata including client_id and portfolio_id.
    """
    logger.info(f"Ingesting analysis for portfolio {client_id}/{portfolio_id} into ChromaDB...")
    try:
        collection = get_rag_collection()
        embedding_function = get_embedding_function()

        # Ensure _id is a string if it's an ObjectId for metadata
        if "_id" in portfolio_data and isinstance(portfolio_data["_id"], ObjectId):
            portfolio_data["_id"] = str(portfolio_data["_id"])

        # Create a unique ID for the document in ChromaDB
        # Using a combination of client_id, portfolio_id, and a timestamp for uniqueness if re-ingested
        doc_id = f"{client_id}-{portfolio_id}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # Combine relevant data into a single string for embedding
        # This string will be the "document" content
        document_content = f"Client ID: {client_id}\n" \
                           f"Portfolio ID: {portfolio_id}\n" \
                           f"Compliance Report Summary: {analysis_report}\n" \
                           f"Portfolio Details: {portfolio_data.get('compliance_report', '')}\n" \
                           f"Positions: {portfolio_data.get('positions', [])}\n" \
                           f"Analysis: {portfolio_data.get('analysis', {})}"


        # Add the document to the collection
        collection.add(
            documents=[document_content],
            metadatas=[{"client_id": client_id, "portfolio_id": portfolio_id}],
            ids=[doc_id]
        )
        logger.info(f"Successfully ingested analysis for portfolio {client_id}/{portfolio_id} into ChromaDB.")
    except Exception as e:
        logger.error(f"Error ingesting portfolio analysis for {client_id}/{portfolio_id}: {e}", exc_info=True)
        raise

async def query_portfolio(client_id: str, portfolio_id: str, question: str) -> str:
    """
    Queries the ChromaDB for information about a specific portfolio
    and uses an LLM to answer a question based on the retrieved context.
    """
    try:
        collection = get_rag_collection()
        embedding_function = get_embedding_function()

        # Normalize client_id and portfolio_id for consistent filtering
        client_id_norm = client_id.strip().upper()
        portfolio_id_norm = portfolio_id.strip().upper()

        # Generate embedding for the question
        query_embedding = embedding_function([question])[0] # embedding_function returns a list of embeddings

        logger.info(f"Querying ChromaDB for portfolio {portfolio_id_norm} with question.")

        # Corrected where clause for ChromaDB to filter by both client_id and portfolio_id
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5, # Retrieve more results to form a richer context
            where={
                "$and": [
                    {"client_id": client_id_norm},
                    {"portfolio_id": portfolio_id_norm}
                ]
            }
        )

        context = ""
        if results and results["documents"]:
            # Flatten the list of lists into a single list of documents, then join
            # results["documents"] is a list of lists, where each inner list contains documents for a given query_embedding
            # Since we have only one query_embedding, we take results["documents"][0]
            context = "\n".join(results["documents"][0])

        logger.debug(f"Context retrieved from ChromaDB for portfolio {portfolio_id_norm}: {context}")

        if not context:
            logger.warning(f"No relevant context found for portfolio {portfolio_id_norm} and question.")
            return "No relevant information found for this portfolio and question."

        prompt = f"""You are a compliance assistant. Based on the following portfolio report:

{context}

Answer the question: "{question}"
"""
        logger.debug(f"Generated prompt:\n{prompt}")

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY environment variable not set.")
            raise Exception("OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable.")

        client = OpenAI(api_key=openai_api_key)

        logger.info(f"Calling OpenAI GPT-4 for portfolio {portfolio_id_norm}...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content.strip()
        logger.info(f"Successfully received answer from OpenAI for portfolio {portfolio_id_norm}.")
        return answer

    except Exception as e:
        logger.error(f"Error during RAG query or OpenAI call for portfolio {client_id}/{portfolio_id}: {e}", exc_info=True)
        # Ensure HTTPException is raised here as it was imported
        raise HTTPException(status_code=500, detail=f"Error processing RAG query: {e}")