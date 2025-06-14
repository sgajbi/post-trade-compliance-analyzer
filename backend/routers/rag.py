import logging 
from fastapi import APIRouter, HTTPException 
from rag_service import query_portfolio 

router = APIRouter() 

logger = logging.getLogger(__name__) 

@router.post("/ask/{portfolio_id}")
async def ask_question(portfolio_id: str, question: str):
    """
    Answers a question about a specific portfolio using the RAG service.
    """
    logger.info(f"Received question for portfolio {portfolio_id}: '{question}'")
    if not portfolio_id:
        raise HTTPException(status_code=400, detail="Portfolio ID must be provided.")
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer = query_portfolio(portfolio_id, question)
        logger.info(f"Successfully answered question for portfolio {portfolio_id}.")
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error answering question for portfolio {portfolio_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {e}")