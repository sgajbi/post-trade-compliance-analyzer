# crud/portfolio_crud.py
import logging
from bson import ObjectId
from db.mongo import portfolio_collection

logger = logging.getLogger(__name__)

async def create_portfolio_doc(portfolio_data: dict) -> str:
    """Inserts a new portfolio document into the database."""
    # Ensure client_id and portfolio_id are present for unique identification later
    if "client_id" not in portfolio_data or "portfolio_id" not in portfolio_data:
        logger.error("Portfolio data must contain 'client_id' and 'portfolio_id'.")
        raise ValueError("Missing 'client_id' or 'portfolio_id' in portfolio data.")

    # Optional: Add a check here if you want to prevent duplicates
    # existing_portfolio = await portfolio_collection.find_one({
    #     "client_id": portfolio_data["client_id"],
    #     "portfolio_id": portfolio_data["portfolio_id"]
    # })
    # if existing_portfolio:
    #     logger.warning(f"Portfolio with client_id {portfolio_data['client_id']} and portfolio_id {portfolio_data['portfolio_id']} already exists.")
    #     # You might want to return existing ID or raise an error
    #     return str(existing_portfolio["_id"])

    result = await portfolio_collection.insert_one(portfolio_data)
    return str(result.inserted_id)

async def get_portfolio_doc_by_mongodb_id(mongo_id: str) -> dict | None:
    """
    Retrieves a single portfolio document by its MongoDB ObjectId.
    Returns None if not found or if the ID is invalid.
    """
    try:
        object_id = ObjectId(mongo_id)
        return await portfolio_collection.find_one({"_id": object_id})
    except Exception:
        logger.warning(f"Invalid MongoDB ID format: {mongo_id}")
        return None

async def get_portfolio_by_client_and_portfolio_id(client_id: str, portfolio_id: str) -> dict | None:
    """
    Retrieves a single portfolio document using client_id and portfolio_id.
    """
    logger.info(f"Attempting to retrieve portfolio for client '{client_id}', portfolio '{portfolio_id}'")
    portfolio = await portfolio_collection.find_one(
        {"client_id": client_id, "portfolio_id": portfolio_id}
    )
    if portfolio:
        logger.info(f"Portfolio found for client '{client_id}', portfolio '{portfolio_id}'.")
    else:
        logger.warning(f"No portfolio found for client '{client_id}', portfolio '{portfolio_id}'.")
    return portfolio

async def update_portfolio_doc(mongo_id: str, update_data: dict) -> bool:
    """
    Updates an existing portfolio document identified by its MongoDB ObjectId.
    Replaces the entire document except for its _id.
    """
    try:
        object_id = ObjectId(mongo_id)
    except Exception:
        logger.warning(f"Invalid ID format for MongoDB update: {mongo_id}. Must be a valid ObjectId string.")
        return False
    # Ensure _id is not in update_data if it's coming from an external source to prevent replacing it
    update_data_copy = update_data.copy()
    update_data_copy.pop("_id", None) # Remove _id if present in the data to be replaced
    result = await portfolio_collection.replace_one({"_id": object_id}, update_data_copy)
    return result.modified_count > 0

async def get_all_portfolio_docs() -> list:
    """Retrieves all portfolio documents."""
    cursor = portfolio_collection.find({})
    return await cursor.to_list(length=None)

async def get_positions_from_portfolio_doc(client_id: str, portfolio_id: str) -> list:
    """
    Retrieves positions for a given portfolio using client_id and portfolio_id.
    """
    doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
    return doc.get("positions", []) if doc else []

async def get_trades_from_portfolio_doc(client_id: str, portfolio_id: str) -> list:
    """
    Retrieves trades for a given portfolio using client_id and portfolio_id.
    """
    doc = await get_portfolio_by_client_and_portfolio_id(client_id, portfolio_id)
    return doc.get("trades", []) if doc else []