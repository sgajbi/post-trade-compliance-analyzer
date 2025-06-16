# routers/rag.py
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel # Import BaseModel for request body validation
from rag_service import query_portfolio

router = APIRouter()

logger = logging.getLogger(__name__)

# Define a Pydantic model for the request body
class ChatRequest(BaseModel):
    question: str
    chat_history: list = [] # Optional, defaults to empty list

@router.post("/ask/{client_id}/{portfolio_id}")
async def ask_question(client_id: str, portfolio_id: str, request: ChatRequest): # Use the Pydantic model
    """
    Answers a question about a specific portfolio using the RAG service, identified by client_id and portfolio_id,
    and supports conversation history for contextual answers.
    """
    logger.info(f"Received question for portfolio {client_id}/{portfolio_id}: '{request.question}'")
    if not client_id or not portfolio_id:
        raise HTTPException(status_code=400, detail="Client ID and Portfolio ID must be provided.")
    if not request.question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Pass both client_id, portfolio_id, current question, and chat_history to query_portfolio
        answer = await query_portfolio(client_id, portfolio_id, request.question, request.chat_history)
        logger.info(f"Successfully answered question for portfolio {client_id}/{portfolio_id}.")
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error answering question for portfolio {client_id}/{portfolio_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {e}")