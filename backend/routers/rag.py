# routers/rag.py
import logging
from fastapi import APIRouter, HTTPException
from rag_service import query_portfolio # Will be updated to take client_id, portfolio_id

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/ask/{client_id}/{portfolio_id}") # CHANGED: Path includes client_id
async def ask_question(client_id: str, portfolio_id: str, question: str): # CHANGED: Parameters
    """
    Answers a question about a specific portfolio using the RAG service, identified by client_id and portfolio_id.
    """
    logger.info(f"Received question for portfolio {client_id}/{portfolio_id}: '{question}'")
    if not client_id or not portfolio_id: # CHANGED: Check both IDs
        raise HTTPException(status_code=400, detail="Client ID and Portfolio ID must be provided.")
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # CHANGED: Pass both client_id and portfolio_id to query_portfolio
        answer = await query_portfolio(client_id, portfolio_id, question)
        logger.info(f"Successfully answered question for portfolio {client_id}/{portfolio_id}.")
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error answering question for portfolio {client_id}/{portfolio_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {e}")