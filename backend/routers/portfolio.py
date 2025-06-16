# routers/portfolio.py
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any # Added 'Dict', 'Any' for historical data response

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
    get_trades_from_portfolio_doc,
    get_historical_portfolio_data # NEW: Import for historical data
)
from utils.serializers import serialize_portfolio_summary, serialize_portfolio_detail # For response serialization
from datetime import datetime, date # Import datetime and date for type checking

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
        logger.error("Uploaded file is not a valid JSON.")
        raise HTTPException(status_code=400, detail="Invalid JSON file provided.")
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")

    # Process the data using the service layer
    try:
        result = await process_uploaded_portfolio_data(portfolio_data)
        logger.info(f"Successfully processed uploaded portfolio for {result['client_id']}/{result['portfolio_id']}")
        return {"message": "Portfolio uploaded and processed successfully", "data": result}
    except ValueError as e:
        logger.error(f"Validation error processing uploaded portfolio: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Runtime error processing uploaded portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing uploaded portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@router.get("/portfolio/{client_id}/{portfolio_id}/summary")
async def get_portfolio_summary(client_id: str, portfolio_id: str):
    logger.info(f"Endpoint: Fetching summary for portfolio {client_id}/{portfolio_id}")
    portfolio_doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
    if not portfolio_doc:
        logger.warning(f"Portfolio {client_id}/{portfolio_id} not found.")
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Serialize the full document to a summary format
    summary_data = serialize_portfolio_summary(portfolio_doc)
    return summary_data

@router.get("/portfolio/{client_id}/{portfolio_id}/detail")
async def get_portfolio_detail(client_id: str, portfolio_id: str):
    logger.info(f"Endpoint: Fetching details for portfolio {client_id}/{portfolio_id}")
    portfolio_doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
    if not portfolio_doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    detail_data = serialize_portfolio_detail(portfolio_doc)
    return detail_data

@router.post("/portfolio/{client_id}/{portfolio_id}/add-trade")
async def add_trade(client_id: str, portfolio_id: str, trade: TradeIn):
    logger.info(f"Endpoint: Adding trade to portfolio {client_id}/{portfolio_id}.")
    try:
        result = await add_trade_and_reanalyze_portfolio(client_id, portfolio_id, trade)
        logger.info(f"Successfully added trade to portfolio {client_id}/{portfolio_id}.")
        return {"message": "Trade added and portfolio re-analyzed successfully", "data": result}
    except ValueError as e:
        logger.error(f"Validation error adding trade: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Runtime error adding trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error adding trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

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

# NEW ENDPOINT: Get Historical Portfolio Data
@router.get("/portfolio/{client_id}/{portfolio_id}/history", response_model=List[Dict[str, Any]])
async def get_portfolio_history(client_id: str, portfolio_id: str):
    logger.info(f"Endpoint: Fetching historical data for portfolio {client_id}/{portfolio_id}")
    historical_data = await get_historical_portfolio_data(client_id, portfolio_id)
    if not historical_data:
        # Optionally, check if portfolio exists at all to differentiate 404 from empty history
        portfolio_doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
        if not portfolio_doc:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return []
    
    # Ensure datetime objects are converted to ISO strings if necessary for JSON serialization
    # This loop is a safeguard; get_historical_portfolio_data already projects simple fields,
    # but if 'date' or 'uploaded_at' were ever retrieved as datetime objects from MongoDB directly
    # without prior serialization, this ensures they are converted.
    for record in historical_data:
        if isinstance(record.get('uploaded_at'), datetime):
            record['uploaded_at'] = record['uploaded_at'].isoformat()
        if isinstance(record.get('date'), date):
            record['date'] = record['date'].isoformat()
    
    return historical_data