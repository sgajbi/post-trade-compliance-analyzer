import json
import logging
from datetime import datetime, date
from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from db.mongo import portfolio_collection
from agents.policy_validator import PolicyValidatorAgent
from agents.risk_drift import RiskDriftAgent
from agents.breach_reporter import BreachReporterAgent
from rag_service import ingest_portfolio_analysis
from utils.serializers import serialize_portfolio_summary, serialize_portfolio_detail
from routers.static_data import get_product_shelf

router = APIRouter()

logger = logging.getLogger(__name__)

# --- Pydantic Models for Portfolio and Trade Data ---
class TradeIn(BaseModel):
    symbol: str
    quantity: float = Field(..., gt=0, description="Quantity of the instrument to trade, must be positive.")
    price: float = Field(..., gt=0, description="Execution price per unit of the instrument, must be positive.")
    trade_date: Optional[date] = None
    type: str = Field("BUY", pattern="^(BUY|SELL)$", description="Type of trade (BUY or SELL).")

class Position(BaseModel):
    isin: str
    symbol: str
    quantity: float
    avg_price: float
    market_price: float
    sector: str

class Trade(BaseModel):
    trade_id: str
    symbol: str
    quantity: float
    price: float
    trade_date: str
    type: str

class PortfolioUpdate(BaseModel):
    client_id: str
    portfolio_id: str
    date: str
    positions: List[Position]
    trades: List[Trade]
    uploaded_at: datetime
    analysis: Optional[dict] = None

@router.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    logger.info(f"Received upload request for file: {file.filename}")
    contents = await file.read()

    try:
        decoded_content = contents.decode("utf-8")
        portfolio_data = json.loads(decoded_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode or parse JSON from file {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON format in uploaded file: {e}")
    except Exception as e:
        logger.error(f"Error reading or decoding file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Error processing uploaded file.")

    mongo_id = ObjectId()
    portfolio_data["_id"] = mongo_id
    portfolio_data["uploaded_at"] = datetime.now()
    portfolio_data["analysis"] = {}

    if "positions" not in portfolio_data or not isinstance(portfolio_data["positions"], list):
        portfolio_data["positions"] = []
    if "trades" not in portfolio_data or not isinstance(portfolio_data["trades"], list):
        portfolio_data["trades"] = []

    try:
        # Convert list of Pydantic Position objects to dictionaries for agents
        # (This block applies if positions are already Pydantic objects,
        # but for initial upload, they come as dicts directly from JSON)
        # This will be handled implicitly if the data remains dicts until agents.
        
        policy_validator = PolicyValidatorAgent(portfolio_data["positions"])
        policy_violations = policy_validator.run()

        risk_drift_analyzer = RiskDriftAgent(portfolio_data["positions"])
        risk_drifts = risk_drift_analyzer.run()

        breach_reporter = BreachReporterAgent(policy_violations, risk_drifts)
        compliance_report = breach_reporter.generate_report()

        portfolio_data["analysis"] = compliance_report
        logger.info(f"Compliance analysis completed for {file.filename}.")

        # Convert compliance_report dictionary to a JSON string for RAG ingestion
        compliance_report_str = json.dumps(compliance_report)
        
        portfolio_identifier = portfolio_data.get("portfolio_id", str(mongo_id))
        ingest_portfolio_analysis(portfolio_identifier, compliance_report_str) # Pass the string
        logger.info(f"Portfolio analysis ingested into RAG for {portfolio_identifier}.")

        result = await portfolio_collection.insert_one(portfolio_data)
        logger.info(f"Portfolio {portfolio_identifier} uploaded and stored with MongoDB ID: {result.inserted_id}")

        return {
            "message": "Portfolio uploaded and analyzed successfully",
            "portfolio_id": portfolio_data.get("portfolio_id", str(mongo_id)),
            "mongo_id": str(result.inserted_id),
            "filename": file.filename,
            "analysis": compliance_report
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An error occurred during portfolio upload and analysis for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during processing: {e}")

@router.get("/portfolios")
async def get_all_portfolios():
    logger.info("Fetching all portfolios summary...")
    try:
        cursor = portfolio_collection.find({})
        portfolios = []
        async for portfolio in cursor:
            summary = serialize_portfolio_summary(portfolio)
            if summary:
                portfolios.append(summary)
            else:
                logger.warning(f"Failed to serialize portfolio: {portfolio.get('_id')}")
        logger.info(f"Successfully retrieved {len(portfolios)} portfolio summaries.")
        return portfolios
    except Exception as e:
        logger.error(f"Error fetching all portfolios: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolios: {e}")

@router.get("/portfolio/{id}")
async def get_portfolio(id: str):
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
        raise
    except Exception as e:
        logger.error(f"Error retrieving portfolio {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio: {e}")

@router.post("/portfolio/{portfolio_mongo_id}/add-trade")
async def add_trade_to_portfolio(portfolio_mongo_id: str, trade_in: TradeIn):
    logger.info(f"Received trade addition request for portfolio {portfolio_mongo_id}: {trade_in.dict()}")

    try:
        object_id = ObjectId(portfolio_mongo_id)
    except Exception:
        logger.warning(f"Invalid portfolio_mongo_id format provided: {portfolio_mongo_id}")
        raise HTTPException(status_code=400, detail="Invalid Portfolio ID format")

    try:
        portfolio_doc = await portfolio_collection.find_one({"_id": object_id})
        if not portfolio_doc:
            logger.warning(f"Portfolio with MongoDB ID {portfolio_mongo_id} not found for trade addition.")
            raise HTTPException(status_code=404, detail="Portfolio not found")

        portfolio_doc["id"] = str(portfolio_doc["_id"])
        del portfolio_doc["_id"]
        if isinstance(portfolio_doc["uploaded_at"], str):
             portfolio_doc["uploaded_at"] = datetime.fromisoformat(portfolio_doc["uploaded_at"])
        if isinstance(portfolio_doc["date"], date):
             portfolio_doc["date"] = portfolio_doc["date"].isoformat()
        elif not isinstance(portfolio_doc["date"], str):
             portfolio_doc["date"] = str(portfolio_doc["date"])

        current_portfolio = PortfolioUpdate(**portfolio_doc)

        product_shelf = await get_product_shelf()
        instrument_details = next(
            (p for p in product_shelf if p["symbol"].upper() == trade_in.symbol.upper()),
            None
        )

        if not instrument_details:
            logger.warning(f"Instrument {trade_in.symbol} not found in product shelf.")
            raise HTTPException(status_code=404, detail=f"Instrument '{trade_in.symbol}' not found in product shelf.")

        updated_positions = []
        found_position = False
        for pos in current_portfolio.positions:
            if pos.symbol.upper() == trade_in.symbol.upper():
                if trade_in.type == "BUY":
                    new_quantity = pos.quantity + trade_in.quantity
                    new_avg_price = ((pos.quantity * pos.avg_price) + (trade_in.quantity * trade_in.price)) / new_quantity
                else:
                     logger.error(f"Trade type '{trade_in.type}' not yet supported for position update.")
                     raise HTTPException(status_code=400, detail=f"Trade type '{trade_in.type}' not supported.")

                pos.quantity = new_quantity
                pos.avg_price = new_avg_price
                pos.market_price = instrument_details["market_price"]
                pos.sector = instrument_details["sector"]
                updated_positions.append(pos)
                found_position = True
            else:
                updated_positions.append(pos)

        if not found_position and trade_in.type == "BUY":
            new_position = Position(
                isin=instrument_details["isin"],
                symbol=instrument_details["symbol"],
                quantity=trade_in.quantity,
                avg_price=trade_in.price,
                market_price=instrument_details["market_price"],
                sector=instrument_details["sector"]
            )
            updated_positions.append(new_position)
        elif not found_position and trade_in.type == "SELL":
             logger.error(f"Cannot perform SELL trade for a non-existent position for instrument {trade_in.symbol}.")
             raise HTTPException(status_code=400, detail=f"Cannot perform SELL trade for non-existent position '{trade_in.symbol}'.")

        current_portfolio.positions = updated_positions

        new_trade_id = f"T{len(current_portfolio.trades) + 1:04d}"
        new_trade = Trade(
            trade_id=new_trade_id,
            symbol=trade_in.symbol,
            quantity=trade_in.quantity,
            price=trade_in.price,
            trade_date= (trade_in.trade_date or date.today()).isoformat(),
            type=trade_in.type
        )
        current_portfolio.trades.append(new_trade)

        # Convert list of Position Pydantic models to list of dictionaries for agents
        positions_as_dicts = [pos.dict(by_alias=True, exclude_none=True) for pos in current_portfolio.positions]

        policy_validator = PolicyValidatorAgent(positions_as_dicts)
        policy_violations = policy_validator.run()

        risk_drift_analyzer = RiskDriftAgent(positions_as_dicts)
        risk_drifts = risk_drift_analyzer.run()

        breach_reporter = BreachReporterAgent(policy_violations, risk_drifts)
        compliance_report = breach_reporter.generate_report()

        current_portfolio.analysis = compliance_report
        logger.info(f"Compliance analysis re-run for portfolio {portfolio_mongo_id} after trade.")

        # Convert compliance_report dictionary to a JSON string for RAG ingestion
        compliance_report_str = json.dumps(compliance_report)

        portfolio_identifier_for_rag = current_portfolio.portfolio_id or str(object_id)
        ingest_portfolio_analysis(portfolio_identifier_for_rag, compliance_report_str) # Pass the string
        logger.info(f"Updated portfolio analysis re-ingested into RAG for {portfolio_identifier_for_rag}.")

        update_doc = current_portfolio.dict(by_alias=True, exclude_none=True)
        update_doc["_id"] = object_id
        if "id" in update_doc:
            del update_doc["id"]

        result = await portfolio_collection.replace_one({"_id": object_id}, update_doc)

        if result.modified_count == 0:
            logger.warning(f"Portfolio {portfolio_mongo_id} not modified during trade addition. It might not exist or data was identical.")

        logger.info(f"Trade added and portfolio {portfolio_mongo_id} updated successfully.")
        return {
            "message": "Trade added and portfolio updated successfully",
            "portfolio_id": current_portfolio.portfolio_id,
            "mongo_id": str(object_id),
            "new_trade_id": new_trade_id,
            "analysis": compliance_report
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An error occurred during trade addition for portfolio {portfolio_mongo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during trade addition: {e}")