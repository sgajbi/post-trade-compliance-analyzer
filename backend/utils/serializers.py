import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

def serialize_portfolio_summary(portfolio):
    """
    Serializes a portfolio document for summary display, converting ObjectId to str.
    """
    if not isinstance(portfolio, dict):
        logger.error(f"Expected dict for serialization, got {type(portfolio)}")
        return None
    return {
        "id": str(portfolio.get("_id")),
        "client_id": portfolio.get("client_id"),
        "portfolio_id": portfolio.get("portfolio_id"),
        "date": portfolio.get("date"),
        "uploaded_at": portfolio.get("uploaded_at")
    }

def serialize_portfolio_detail(portfolio):
    """
    Serializes a detailed portfolio document, converting ObjectId to str and removing original _id.
    """
    if not isinstance(portfolio, dict):
        logger.error(f"Expected dict for serialization, got {type(portfolio)}")
        return None
    portfolio_copy = portfolio.copy()
    if "_id" in portfolio_copy:
        portfolio_copy["id"] = str(portfolio_copy["_id"])
        del portfolio_copy["_id"]
    return portfolio_copy