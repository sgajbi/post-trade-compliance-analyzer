import logging
from datetime import datetime, date
from bson import ObjectId
import uuid
from typing import List, Dict, Optional

from crud.portfolio_crud import create_portfolio_doc, get_portfolio_by_client_and_portfolio_id, update_portfolio_doc
from agents.policy_validator import PolicyValidatorAgent
from agents.risk_drift import RiskDriftAgent
from agents.breach_reporter import BreachReporterAgent
from rag_service import ingest_portfolio_analysis
from schemas.portfolio_models import TradeIn, Position # Assuming TradeIn and Position are Pydantic models

logger = logging.getLogger(__name__)

# Helper function to convert ObjectId fields to strings in a dictionary
def _convert_objectid_to_str(doc: dict) -> dict:
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc

# NEW HELPER FUNCTION: Calculate positions from trades
def _calculate_positions_from_trades(trades: List[Dict]) -> List[Dict]:
    """
    Calculates current positions based on a list of trades.
    Aggregates quantities for each symbol and adds placeholder/derived values for other fields.
    """
    symbol_data = {} # To store aggregated quantity, and placeholder for other details

    for trade in trades:
        symbol = trade.get("symbol")
        quantity = trade.get("quantity")
        trade_type = trade.get("type") # 'BUY' or 'SELL'
        trade_price = trade.get("price") # Get the price from the trade
        
        # Extract ISIN and Sector from the trade, if provided
        trade_isin = trade.get("isin")
        trade_sector = trade.get("sector")
        # Capture the latest trade price as a potential market price placeholder
        latest_trade_price = trade.get("price")


        if not all([symbol, isinstance(quantity, (int, float)), trade_type]):
            logger.warning(f"Skipping malformed trade data: {trade}")
            continue

        if symbol not in symbol_data:
            symbol_data[symbol] = {
                "quantity": 0,
                "prices": [], # To calculate average price, if needed
                "isin": "UNKNOWN", # Default placeholder
                "sector": "UNKNOWN", # Default placeholder
                "latest_price": 0.0 # Initialize latest_price for market_price placeholder
            }
            # If this is the first trade for the symbol, use ISIN/Sector from it if available
            if trade_isin:
                symbol_data[symbol]["isin"] = trade_isin
            if trade_sector:
                symbol_data[symbol]["sector"] = trade_sector
        else:
            # If symbol already exists, and the new trade has ISIN/Sector, update if currently UNKNOWN
            # Or implement a policy for consistent data (e.g., first one wins, or raise warning on mismatch)
            if symbol_data[symbol]["isin"] == "UNKNOWN" and trade_isin:
                symbol_data[symbol]["isin"] = trade_isin
            if symbol_data[symbol]["sector"] == "UNKNOWN" and trade_sector:
                symbol_data[symbol]["sector"] = trade_sector

        current_quantity = symbol_data[symbol]["quantity"]

        if trade_type.upper() == "BUY":
            symbol_data[symbol]["quantity"] += quantity
            if trade_price is not None:
                symbol_data[symbol]["prices"].append({"quantity": quantity, "price": trade_price})
                symbol_data[symbol]["latest_price"] = trade_price # Update latest price on BUY
        elif trade_type.upper() == "SELL":
            symbol_data[symbol]["quantity"] -= quantity
            # Update latest price on SELL too, if desired, or keep only BUY price for 'market_price'
            if trade_price is not None:
                symbol_data[symbol]["latest_price"] = trade_price
        else:
            logger.warning(f"Unknown trade type '{trade_type}' for symbol {symbol}. Skipping.")

    # Convert aggregated quantities and collected data into a list of position dictionaries
    positions = []
    for symbol, data in symbol_data.items():
        total_quantity = data["quantity"]
        
        if total_quantity != 0: # Only include positions with non-zero quantity
            total_value = sum(item["quantity"] * item["price"] for item in data["prices"] if item["price"] is not None)
            total_bought_quantity = sum(item["quantity"] for item in data["prices"])
            
            avg_price = total_value / total_bought_quantity if total_bought_quantity > 0 else 0
            
            # Use the latest_price captured from trades as a placeholder for market_price
            market_price = data["latest_price"] if data["latest_price"] != 0.0 else avg_price

            positions.append({
                "symbol": symbol,
                "quantity": total_quantity,
                "isin": data["isin"], # Use provided ISIN or default
                "avg_price": avg_price,
                "market_price": market_price, # Now uses latest trade price or avg if no trades with price
                "sector": data["sector"] # Use provided Sector or default
            })

    return positions

async def process_uploaded_portfolio_data(portfolio_data: dict) -> dict:
    """
    Processes uploaded portfolio data, runs compliance analysis, stores it,
    and ingests analysis into the RAG system.
    """
    logger.info("Service: Starting to process uploaded portfolio data.")

    # 1. Extract positions and basic info
    # For uploaded data, if trades are present, recalculate positions
    if "trades" in portfolio_data and isinstance(portfolio_data["trades"], list):
        # Ensure all trades have a trade_id, especially for uploaded data
        for trade in portfolio_data["trades"]:
            if "trade_id" not in trade:
                trade["trade_id"] = str(uuid.uuid4()) # Assign a unique ID
            # Convert datetime.date to ISO 8601 string for MongoDB compatibility
            if isinstance(trade.get('trade_date'), date):
                trade['trade_date'] = trade['trade_date'].isoformat()
        
        # Calculate positions from the provided trades
        portfolio_data["positions"] = _calculate_positions_from_trades(portfolio_data["trades"])
        logger.info(f"Recalculated positions for uploaded portfolio based on trades: {portfolio_data['positions']}")
    else:
        # If no trades, use existing positions or default to empty list
        portfolio_data["positions"] = portfolio_data.get("positions", [])
        logger.info(f"Using provided positions for uploaded portfolio: {portfolio_data['positions']}")


    positions = portfolio_data.get("positions", [])
    client_id = portfolio_data.get("client_id")
    portfolio_id = portfolio_data.get("portfolio_id")

    if not client_id or not portfolio_id:
        logger.error("Uploaded portfolio data missing 'client_id' or 'portfolio_id'.")
        raise ValueError("Portfolio data must contain 'client_id' or 'portfolio_id'.")

    # 2. Run Policy Validation
    policy_validator = PolicyValidatorAgent(positions=positions)
    policy_violations = policy_validator.run()
    logger.info(f"Policy validation completed for {client_id}/{portfolio_id}. Violations: {len(policy_violations)}")

    # 3. Run Risk Drift Analysis
    risk_drift_analyzer = RiskDriftAgent(positions=positions)
    risk_drifts = risk_drift_analyzer.run()
    logger.info(f"Risk drift analysis completed for {client_id}/{portfolio_id}. Drifts: {len(risk_drifts)}")

    # 4. Generate Breach Report
    breach_reporter = BreachReporterAgent(
        policy_violations=policy_violations, risk_drifts=risk_drifts
    )
    compliance_report = breach_reporter.generate_report()
    logger.info(f"Breach report generated for {client_id}/{portfolio_id}.")

    # 5. Prepare data for storage and ingest
    # Add analysis results and timestamp to the portfolio data
    portfolio_data["analysis"] = {
        "policy_violations": policy_violations,
        "risk_drifts": risk_drifts,
    }
    portfolio_data["compliance_report"] = compliance_report
    portfolio_data["uploaded_at"] = datetime.now().isoformat() # Timestamp when uploaded/processed


    # 6. Store portfolio data in MongoDB (create or update)
    # Check if a portfolio with the same client_id and portfolio_id already exists
    existing_portfolio_doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)

    if existing_portfolio_doc:
        logger.info(f"Existing portfolio found for {client_id}/{portfolio_id}. Updating document.")
        # Update the existing document
        mongo_id = existing_portfolio_doc["_id"] # Get the existing MongoDB ObjectId
        success = await update_portfolio_doc(str(mongo_id), portfolio_data)
        if not success:
            logger.error(f"Failed to update existing portfolio {client_id}/{portfolio_id}.")
            raise RuntimeError("Failed to update existing portfolio in database.")
        portfolio_mongo_id = str(mongo_id) # Use the existing ID
        # IMPORTANT: If portfolio_data was merged from existing_portfolio_doc,
        # ensure its _id is stringified before JSON dumps.
        _convert_objectid_to_str(portfolio_data) # Convert _id to string for RAG ingestion
    else:
        logger.info(f"No existing portfolio found for {client_id}/{portfolio_id}. Creating new document.")
        # Create a new document
        portfolio_mongo_id = await create_portfolio_doc(portfolio_data)
        if not portfolio_mongo_id:
            logger.error(f"Failed to create new portfolio for {client_id}/{portfolio_id}.")
            raise RuntimeError("Failed to create new portfolio in database.")
        # For a new document, create_portfolio_doc returns a string ID, so no conversion needed for _id.

    logger.info(f"Portfolio {client_id}/{portfolio_id} stored/updated with MongoDB ID: {portfolio_mongo_id}")

    # 7. Ingest analysis into RAG
    # portfolio_data (which might have come from DB) must have ObjectId converted to string
    await ingest_portfolio_analysis(
        client_id,
        portfolio_data, # This dict must now be JSON serializable
        analysis_report=compliance_report,
        portfolio_id=portfolio_id
    )
    logger.info(f"Analysis for {client_id}/{portfolio_id} ingested into RAG.")

    # Return the compliance report and the MongoDB ID
    return {
        "mongo_id": portfolio_mongo_id,
        "client_id": client_id,
        "portfolio_id": portfolio_id,
        "analysis": portfolio_data["analysis"],
        "compliance_report": compliance_report,
    }

async def add_trade_and_reanalyze_portfolio(client_id: str, portfolio_id: str, trade_in: TradeIn):
    logger.info(f"Service: Adding trade to portfolio {client_id}/{portfolio_id} and re-analyzing.")

    existing_portfolio = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
    if not existing_portfolio:
        logger.warning(f"Portfolio {client_id}/{portfolio_id} not found for trade addition.")
        raise ValueError(f"Portfolio {client_id}/{portfolio_id} not found.")

    # Convert ObjectId to string for JSON serialization before further processing
    _convert_objectid_to_str(existing_portfolio)

    # Ensure positions and trades lists exist
    if "positions" not in existing_portfolio or existing_portfolio["positions"] is None:
        existing_portfolio["positions"] = []
    if "trades" not in existing_portfolio or existing_portfolio["trades"] is None:
        existing_portfolio["trades"] = []

    # Add the new trade
    trade_data = trade_in.dict()
    # Generate a unique trade_id
    trade_data["trade_id"] = str(uuid.uuid4()) # Add a unique trade_id

    # Convert datetime.date to ISO 8601 string for MongoDB compatibility
    if isinstance(trade_data.get('trade_date'), date):
        trade_data['trade_date'] = trade_data['trade_date'].isoformat()
    existing_portfolio["trades"].append(trade_data)

    # NEW: Recalculate positions based on the updated list of trades
    existing_portfolio["positions"] = _calculate_positions_from_trades(existing_portfolio["trades"])
    logger.info(f"Recalculated positions after trade addition: {existing_portfolio['positions']}")

    # Re-run policy validation and risk drift analysis with updated positions
    updated_positions = existing_portfolio.get("positions", []) # Use the newly calculated positions
    
    policy_validator = PolicyValidatorAgent(positions=updated_positions)
    policy_violations = policy_validator.run()

    risk_drift_analyzer = RiskDriftAgent(positions=updated_positions)
    risk_drifts = risk_drift_analyzer.run()

    breach_reporter = BreachReporterAgent(
        policy_violations=policy_violations, risk_drifts=risk_drifts
    )
    compliance_report = breach_reporter.generate_report()

    existing_portfolio["analysis"] = {
        "policy_violations": policy_violations,
        "risk_drifts": risk_drifts,
    }
    existing_portfolio["compliance_report"] = compliance_report
    existing_portfolio["last_reanalyzed_at"] = datetime.now().isoformat()

    # Get the MongoDB _id from the existing_portfolio
    mongo_id = existing_portfolio.pop("id", None) or existing_portfolio.get("_id")
    if not mongo_id:
        logger.error(f"MongoDB ID not found for portfolio {client_id}/{portfolio_id}.")
        raise ValueError("Portfolio ID missing for update.")
    
    # Update the document in MongoDB
    # Ensure mongo_id is str for update_portfolio_doc
    if isinstance(mongo_id, ObjectId):
        mongo_id = str(mongo_id)
    success = await update_portfolio_doc(mongo_id, existing_portfolio)

    if not success:
        logger.error(f"Failed to update portfolio {client_id}/{portfolio_id} after trade addition.")
        raise RuntimeError("Failed to update portfolio in database.")

    # Ingest the updated analysis into RAG
    await ingest_portfolio_analysis(
        client_id, # New positional argument
        existing_portfolio, # This dict now has _id as str
        analysis_report=compliance_report,
        portfolio_id=portfolio_id
    )
    logger.info(f"Successfully re-analyzed and ingested updated portfolio {client_id}/{portfolio_id}.")
    
    # Return the updated compliance report and other relevant info
    return {
        "client_id": client_id,
        "portfolio_id": portfolio_id,
        "trade_added": trade_data,
        "analysis": existing_portfolio["analysis"],
        "compliance_report": compliance_report,
    }