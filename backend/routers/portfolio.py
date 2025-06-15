# routers/portfolio.py
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from schemas.portfolio_models import TradeIn, Position, Trade # Import models
from services.portfolio_service import ( # Import service functions
    process_uploaded_portfolio_data,
    add_trade_and_reanalyze_portfolio
)
from crud.portfolio_crud import ( # Import CRUD functions for direct data retrieval
    get_portfolio_by_client_and_portfolio_id, # Corrected import name
    get_portfolio_doc_by_mongodb_id,
    get_all_portfolio_docs,
    get_positions_from_portfolio_doc,
    get_trades_from_portfolio_doc
)
from utils.serializers import serialize_portfolio_summary, serialize_portfolio_detail # For response serialization

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    logger.info(f"Endpoint: Received upload request for file: {file.filename}")
    # In a real application, you'd likely parse the file content here (e.g., CSV, JSON)
    # and pass the parsed data (dict) to the service layer.
    file_content = await file.read()
    
    # Assuming the uploaded file is a JSON string representing the portfolio_data
    try:
        import json
        portfolio_data = json.loads(file_content)
    except json.JSONDecodeError:
        logger.error("Uploaded file is not a valid JSON. Please upload a JSON file.")
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a JSON file.")

    # Pass the parsed dictionary to the service layer
    return await process_uploaded_portfolio_data(portfolio_data)


@router.get("/portfolios")
async def get_all_portfolios():
    logger.info("Endpoint: Fetching all portfolios summary...")
    docs = await get_all_portfolio_docs()
    return [serialize_portfolio_summary(doc) for doc in docs if serialize_portfolio_summary(doc)]

@router.get("/portfolio/{client_id}/{portfolio_id}", response_model=dict)
async def get_portfolio_details(client_id: str, portfolio_id: str):
    logger.info(f"Endpoint: Fetching details for portfolio {client_id}/{portfolio_id}")
    portfolio_doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
    if not portfolio_doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return serialize_portfolio_detail(portfolio_doc)


@router.post("/portfolio/{client_id}/{portfolio_id}/add-trade") # CORRECTED: Changed 'add_trade' to 'add-trade'
async def add_trade(client_id: str, portfolio_id: str, trade: TradeIn):
    logger.info(f"Endpoint: Adding trade to portfolio {client_id}/{portfolio_id}: {trade.dict()}")
    try:
        await add_trade_and_reanalyze_portfolio(client_id, portfolio_id, trade)
        return {"message": "Trade added and portfolio re-analyzed successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding trade to portfolio {client_id}/{portfolio_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add trade and re-analyze portfolio.")

@router.get("/portfolio/{client_id}/{portfolio_id}/positions", response_model=List[Position])
async def get_portfolio_positions(client_id: str, portfolio_id: str):
    logger.info(f"Endpoint: Fetching positions for portfolio {client_id}/{portfolio_id}")
    positions_data = await get_positions_from_portfolio_doc(client_id, portfolio_id)
    if not positions_data:
        # Check if the portfolio exists at all, even if it has no positions
        portfolio_doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
        if not portfolio_doc:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return []
    return [Position(**pos) for pos in positions_data]

@router.get("/portfolio/{client_id}/{portfolio_id}/transactions", response_model=List[Trade])
async def get_portfolio_transactions(client_id: str, portfolio_id: str):
    logger.info(f"Endpoint: Fetching transactions (trades) for portfolio {client_id}/{portfolio_id}")
    trades_data = await get_trades_from_portfolio_doc(client_id, portfolio_id)
    if not trades_data:
        # Check if the portfolio exists at all, even if it has no trades
        portfolio_doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
        if not portfolio_doc:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return []
    return [Trade(**trade) for trade in trades_data]