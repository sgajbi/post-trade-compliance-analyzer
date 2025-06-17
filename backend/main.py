import logging
import json # Import json for file operations
import os   # Import os for path operations
from datetime import datetime # Import datetime for timestamps
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import static_data
from routers import portfolio
from routers import rag
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from rag_service import (
    set_rag_components,
    CHROMA_DB_PATH,
    COLLECTION_NAME,
)
from db.mongo import portfolio_collection # Import portfolio_collection

# --- Logging Setup ---
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s" # CHANGE THIS LINE
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Lifespan events for initializing and cleaning up resources
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Initializing RAG components...")
    try:
        # Initialize ChromaDB PersistentClient
        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        logger.info(f"Initialized ChromaDB PersistentClient at {CHROMA_DB_PATH}")

        # Initialize the SentenceTransformer model for embeddings
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info(f"Loaded SentenceTransformer model 'all-MiniLM-L6-v2' and created embedding function.")

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

        # Get or create the collection for portfolio analysis
        collection = chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,  # Use the wrapped embedding function
        )
        logger.info(
            f"Successfully got or created ChromaDB collection: {COLLECTION_NAME}"
        )

        # Set the global RAG components in rag_service
        set_rag_components(chroma_client, ef, collection)
        logger.info("RAG components passed to rag_service.")

    except Exception as e:
        logger.error(
            f"Failed to initialize RAG components during startup: {e}", exc_info=True
        )
        raise

    # --- New: Initialize portfolios from clients.json at startup ---
    logger.info("Initializing portfolios from clients.json if they don't exist...")
    current_dir = os.path.dirname(__file__)
    clients_file_path = os.path.join(current_dir, 'data', 'clients.json')

    try:
        with open(clients_file_path, "r", encoding="utf-8") as f:
            clients_data = json.load(f)

        for client_info in clients_data:
            client_id = client_info.get("client_id")
            portfolios = client_info.get("portfolios", [])

            if not client_id:
                logger.warning(f"Skipping client with missing 'client_id': {client_info}")
                continue

            for portfolio_info in portfolios:
                portfolio_id = portfolio_info.get("portfolio_id")
                if not portfolio_id:
                    logger.warning(f"Skipping portfolio with missing 'portfolio_id' for client {client_id}: {portfolio_info}")
                    continue

                # Check if portfolio already exists in MongoDB
                existing_portfolio = await portfolio_collection.find_one({
                    "client_id": client_id,
                    "portfolio_id": portfolio_id
                })

                if existing_portfolio:
                    logger.info(f"Portfolio {client_id}/{portfolio_id} already exists. Skipping initialization.")
                else:
                    # Create a new empty portfolio document
                    new_portfolio_doc = {
                        "client_id": client_id,
                        "portfolio_id": portfolio_id,
                        "date": datetime.now().isoformat(), # Current date for creation
                        "uploaded_at": datetime.now().isoformat(), # Timestamp of creation
                        "positions": [], # Initially empty
                        "trades": [],    # Initially empty
                        "analysis": { # Placeholder analysis as there's no data yet
                            "policy_violations": ["No policy data available for analysis yet."],
                            "risk_drifts": ["No risk data available for analysis yet."]
                        }
                    }
                    try:
                        result = await portfolio_collection.insert_one(new_portfolio_doc)
                        logger.info(f"Initialized empty portfolio {client_id}/{portfolio_id} with ID: {result.inserted_id}")
                    except Exception as e:
                        logger.error(f"Error inserting portfolio {client_id}/{portfolio_id} at startup: {e}", exc_info=True)

    except FileNotFoundError:
        logger.error(f"Clients file not found at {clients_file_path}. Skipping portfolio initialization from JSON.")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding clients.json at startup: {e}. Please check file format.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during portfolio initialization from clients.json: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown: Cleaning up resources (if any)..")


# Include routers
app.include_router(static_data.router)
app.include_router(portfolio.router)
app.include_router(rag.router, prefix="/rag")


@app.get("/")
def read_root():
    """
    Root endpoint to confirm the backend is running.
    """
    return {"message": "Post-Trade Compliance Analyzer backend is running"}