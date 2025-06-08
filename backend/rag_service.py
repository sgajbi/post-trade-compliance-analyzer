import chromadb
from chromadb.utils import embedding_functions 
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os
import logging

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Initialize ChromaDB and embedding model ---
# Use PersistentClient for data to be saved to disk
# Ensure the directory exists or is writable by the application
CHROMA_DB_PATH = "./chroma_db"
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    logger.info(f"Initialized ChromaDB PersistentClient at {CHROMA_DB_PATH}")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB PersistentClient: {e}")
    # Depending on your application's tolerance, you might want to exit or raise
    raise

# Initialize the SentenceTransformer model for embeddings
try:
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Loaded SentenceTransformer model 'all-MiniLM-L6-v2'")
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer model: {e}")
    raise

# Get or create the collection for portfolio analysis
COLLECTION_NAME = "portfolio_analysis"
try:
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    logger.info(f"Accessed/Created ChromaDB collection: {COLLECTION_NAME}")
except Exception as e:
    logger.error(f"Failed to get or create ChromaDB collection '{COLLECTION_NAME}': {e}")
    raise


def ingest_portfolio_analysis(portfolio_id: str, analysis_text: str):
    """
    Ingests portfolio analysis text into the ChromaDB collection.
    Splits the text into lines, generates embeddings, and adds them to the vector store.
    """
    if not portfolio_id or not analysis_text:
        logger.warning("Attempted to ingest empty portfolio_id or analysis_text.")
        return

    portfolio_id_norm = portfolio_id.strip().lower()

    # Split analysis text into lines, filter out empty lines
    lines = [line.strip() for line in analysis_text.split("\n") if line.strip()]

    if not lines:
        logger.info(f"No content lines to ingest for portfolio {portfolio_id_norm}.")
        return

    try:
        embeddings = embedding_model.encode(lines).tolist()
        ids = [f"{portfolio_id_norm}_{i}" for i in range(len(lines))]
        metadatas = [{"portfolio_id": portfolio_id_norm} for _ in lines]

        collection.add(documents=lines, ids=ids, embeddings=embeddings, metadatas=metadatas)
        logger.info(f"Ingested {len(lines)} lines for portfolio {portfolio_id_norm} into ChromaDB.")
        for line in lines:
            logger.debug(f"  → Ingested line: {line}") # Use debug for verbose output
    except Exception as e:
        logger.error(f"Error during ingestion for portfolio {portfolio_id_norm}: {e}", exc_info=True)
        raise

def query_portfolio(portfolio_id: str, question: str, top_k: int = 3) -> str:
    """
    Queries the ChromaDB for relevant context related to a specific portfolio and question,
    then uses an LLM (OpenAI GPT-4) to answer the question based on the retrieved context.
    """
    if not portfolio_id or not question:
        logger.warning("Attempted to query with empty portfolio_id or question.")
        return "Please provide a valid portfolio ID and question."

    portfolio_id_norm = portfolio_id.strip().lower()
    logger.info(f"Querying RAG for portfolio_id={portfolio_id_norm}, question='{question}'")

    # Debug: print all documents to check what's stored (can be noisy in production)
    # logger.debug("\n[DEBUG] All stored documents:")
    # all_docs = collection.get(include=["metadatas", "documents", "ids"])
    # for doc, meta in zip(all_docs["documents"], all_docs["metadatas"]):
    #     logger.debug(f" → {doc} | {meta}")

    try:
        # Query with metadata filter to restrict results to the specific portfolio
        results = collection.query(
            query_texts=[question], n_results=top_k, where={"portfolio_id": portfolio_id_norm}
        )

        raw_docs = results.get("documents", [[]])[0] if results.get("documents") else []

        # Clean and filter documents
        # Note: 'strip('",')' should be carefully considered if quotes/commas can be valid content
        # And the 'risk_drifts' filter is specific to your report format.
        cleaned_docs = [
            line.strip().strip('",')
            for line in raw_docs
            if line.strip() and not line.strip().startswith("risk_drifts")
        ]

        context = "\n".join(cleaned_docs)
        logger.debug(f"Retrieved context for portfolio {portfolio_id_norm}:\n{context}")

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
            model="gpt-4", # Consider using a newer model if available and suitable
            messages=[{"role": "user", "content": prompt}]
        )
        
        answer = response.choices[0].message.content.strip()
        logger.info(f"Successfully received answer from OpenAI for portfolio {portfolio_id_norm}.")
        return answer

    except Exception as e:
        logger.error(f"Error during RAG query or OpenAI call for portfolio {portfolio_id_norm}: {e}", exc_info=True)
        raise # Re-raise the exception to be handled by the FastAPI endpoint