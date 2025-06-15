import json
import logging
from datetime import datetime, date # Ensure 'date' is imported
from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, HTTPException
from db.mongo import portfolio_collection
from agents.policy_validator import PolicyValidatorAgent
from agents.risk_drift import RiskDriftAgent
from agents.breach_reporter import BreachReporterAgent
from rag_service import ingest_portfolio_analysis
from utils.serializers import serialize_portfolio_summary, serialize_portfolio_detail

# --- Pydantic Models for Input Validation ---
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

class Position(BaseModel):
    isin: str
    symbol: str
    quantity: int = Field(..., gt=0) # quantity must be greater than 0
    avg_price: float = Field(..., ge=0) # price must be greater than or equal to 0
    market_price: float = Field(..., ge=0)
    sector: str

class Trade(BaseModel):
    trade_id: str
    symbol: str
    quantity: int
    price: float = Field(..., ge=0)
    trade_date: date # Pydantic parses this to datetime.date
    type: str # Could be Literal["BUY", "SELL"] for stricter validation, but str is fine for now

class PortfolioInput(BaseModel):
    client_id: str
    portfolio_id: str
    date: date # Pydantic parses this to datetime.date
    positions: List[Position]
    trades: Optional[List[Trade]] = [] # Trades are optional, defaults to empty list if not provided


router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    """
    Uploads a portfolio JSON file, processes it through compliance agents,
    ingests analysis into RAG, and stores the record in MongoDB.
    """
    logger.info(f"Received upload request for file: {file.filename}")
    contents = await file.read()

    try:
        portfolio_data_parsed = PortfolioInput.parse_raw(contents)
        portfolio_data = portfolio_data_parsed.model_dump(mode='json') if hasattr(portfolio_data_parsed, 'model_dump') else portfolio_data_parsed.dict()
        
        logger.info(f"Successfully parsed and validated portfolio data for {portfolio_data.get('portfolio_id')}.")

    except ValidationError as e:
        logger.error(f"Validation error for file {file.filename}: {e.errors()}")
        raise HTTPException(status_code=400, detail=f"Invalid portfolio data format: {e.errors()}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode or parse JSON from file {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON format in uploaded file: {e}")
    except Exception as e:
        logger.error(f"Error reading or decoding file {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading or decoding file: {e}")

    # Extract relevant data after validation
    positions = portfolio_data.get("positions", [])
    client_id = portfolio_data.get("client_id")
    portfolio_id = portfolio_data.get("portfolio_id")

    if not portfolio_id:
        logger.warning("Uploaded portfolio data is missing 'portfolio_id'.")
        raise HTTPException(status_code=400, detail="Portfolio data must contain a 'portfolio_id'.")
    if not client_id:
        logger.warning(f"Uploaded portfolio {portfolio_id} data is missing 'client_id'.")
        raise HTTPException(status_code=400, detail="Portfolio data must contain a 'client_id'.")

    # Initialize and run compliance agents
    logger.info(f"Running PolicyValidatorAgent for portfolio {portfolio_id}...")
    policy_validator = PolicyValidatorAgent(positions)
    policy_violations = policy_validator.run()

    logger.info(f"Running RiskDriftAgent for portfolio {portfolio_id}...")
    risk_drift_analyzer = RiskDriftAgent(positions)
    risk_drifts = risk_drift_analyzer.run()

    logger.info(f"Running BreachReporterAgent for portfolio {portfolio_id} to generate report...")
    breach_reporter = BreachReporterAgent(policy_violations, risk_drifts)
    report = breach_reporter.generate_report()

    # Ingest analysis into RAG for natural language querying
    analysis_text = json.dumps(report, indent=2) # Convert report dict to string for RAG
    logger.info(f"Ingesting analysis for portfolio {portfolio_id} into RAG.")
    try:
        ingest_portfolio_analysis(portfolio_id, analysis_text)
        logger.info(f"Analysis for portfolio {portfolio_id} successfully ingested into RAG.")
    except Exception as e:
        logger.error(f"Failed to ingest analysis for portfolio {portfolio_id} into RAG: {e}", exc_info=True)


    # Prepare record for MongoDB
    portfolio_record = {
        "client_id": portfolio_data.get("client_id"),
        "portfolio_id": portfolio_data.get("portfolio_id"),
        "date": portfolio_data.get("date"),
        "positions": positions,
        "trades": portfolio_data.get("trades", []),
        "analysis": report,
        "uploaded_at": datetime.utcnow()
    }
    
    for trade in portfolio_record["trades"]:
        if isinstance(trade.get("trade_date"), date):
            trade["trade_date"] = trade["trade_date"].isoformat()

    logger.info(f"Saving portfolio {portfolio_id} to MongoDB...")
    try:
        await portfolio_collection.insert_one(portfolio_record)
        logger.info(f"Portfolio {portfolio_id} saved to MongoDB successfully.")
    except Exception as e:
        logger.error(f"Failed to save portfolio {portfolio_id} to MongoDB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save portfolio to database: {e}")

    return {
        "filename": file.filename,
        "analysis": report,
        "portfolio_id": portfolio_data.get("portfolio_id"),
        "status": "saved_to_db"
    }


@router.get("/portfolios")
async def get_all_portfolios():
    """
    Retrieves a summary list of all uploaded portfolios, sorted by upload time.
    """
    logger.info("Fetching all portfolios summary...")
    try:
        cursor = portfolio_collection.find().sort("uploaded_at", -1)
        portfolios = []
        async for portfolio in cursor:
            portfolios.append(serialize_portfolio_summary(portfolio))
        logger.info(f"Successfully retrieved {len(portfolios)} portfolios summary.")
        return portfolios
    except Exception as e:
        logger.error(f"Error fetching all portfolios: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolios: {e}")

@router.get("/portfolio/{id}")
async def get_portfolio(id: str):
    """
    Retrieves the detailed record of a single portfolio by its MongoDB ObjectId.
    """
    logger.info(f"Fetching detail for portfolio ID: {id}")
    try:
        object_id = ObjectId(id)
    except Exception:
        logger.warning(f"Invalid ID format provided: {id}")
        raise HTTPException(status_code=400, detail="Invalid ID format")

    try:
        portfolio = await portfolio_collection.find_one({"_id": object_id})
        if not portfolio:
            logger.warning(f"Portfolio with ID {id} not found.")
            raise HTTPException(status_code=404, detail="Portfolio not found")

        serialized_portfolio = serialize_portfolio_detail(portfolio)
        if not serialized_portfolio:
            logger.error(f"Failed to serialize portfolio {id} detail.")
            raise HTTPException(status_code=500, detail="Error processing portfolio data.")

        logger.info(f"Successfully retrieved detail for portfolio ID: {id}")
        return serialized_portfolio
    except HTTPException:
        # Re-raise HTTPExceptions as they are already properly formatted
        raise
    except Exception as e:
        logger.error(f"Error retrieving portfolio {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio: {e}")