import json
import os
import logging 
from fastapi import APIRouter, HTTPException

router = APIRouter()

logger = logging.getLogger(__name__) 

@router.get("/product-shelf") 
async def get_product_shelf():
    """
    Retrieves a list of available investment products (stocks) from a static JSON file.
    """
    logger.info("Fetching product shelf data...")
    try:
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, '..', 'data', 'product_shelf.json')

        with open(file_path, "r", encoding="utf-8") as f:
            product_data = json.load(f)
        logger.info(f"Successfully loaded {len(product_data)} items from product shelf.")
        return product_data
    except FileNotFoundError:
        logger.error(f"Product shelf file not found at {file_path}")
        raise HTTPException(status_code=404, detail="Product shelf data not found.")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding product shelf JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading product shelf data: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching product shelf: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.get("/clients") 
async def get_clients():
    """
    Retrieves a static list of clients and their associated portfolios from a JSON file.
    """
    logger.info("Fetching clients data...")
    try:
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, '..', 'data', 'clients.json')

        with open(file_path, "r", encoding="utf-8") as f:
            clients_data = json.load(f)
        logger.info(f"Successfully loaded {len(clients_data)} clients.")
        return clients_data
    except FileNotFoundError:
        logger.error(f"Clients file not found at {file_path}")
        raise HTTPException(status_code=404, detail="Clients data not found.")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding clients JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading clients data: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching clients: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")