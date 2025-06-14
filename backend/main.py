import json
import logging
from datetime import datetime
from bson import ObjectId
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents.policy_validator import PolicyValidatorAgent
from agents.risk_drift import RiskDriftAgent
from agents.breach_reporter import BreachReporterAgent
from db.mongo import portfolio_collection
import os  
from utils.serializers import serialize_portfolio_summary, serialize_portfolio_detail  
from routers import static_data


from rag_service import ingest_portfolio_analysis
from rag_service import query_portfolio

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(static_data.router)

@app.get("/")
def read_root():
    """
    Root endpoint to confirm the backend is running.
    """
    return {"message": "Post-Trade Compliance Analyzer backend is running"}



@app.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    """
    Uploads a portfolio JSON file, processes it through compliance agents,
    ingests analysis into RAG, and stores the record in MongoDB.
    """
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
        raise HTTPException(status_code=500, detail=f"Error processing uploaded file: {e}")

    # Basic validation for critical fields
    portfolio_id = portfolio_data.get("portfolio_id")
    if not portfolio_id:
        logger.warning(f"Uploaded portfolio from {file.filename} missing 'portfolio_id'.")
        raise HTTPException(status_code=400, detail="Portfolio data must contain a 'portfolio_id'.")
        
    positions = portfolio_data.get("positions", [])
    if not isinstance(positions, list):
        logger.warning(f"Portfolio {portfolio_id} has 'positions' not as a list.")
        raise HTTPException(status_code=400, detail="'positions' field must be a list.")

    # === Agents Execution ===
    try:
        logger.info(f"Running PolicyValidatorAgent for portfolio {portfolio_id}...")
        policy_violations = PolicyValidatorAgent(positions).run()
        logger.info(f"Running RiskDriftAgent for portfolio {portfolio_id}...")
        risk_drifts = RiskDriftAgent(positions).run()
        logger.info(f"Generating breach report for portfolio {portfolio_id}...")
        report = BreachReporterAgent(policy_violations, risk_drifts).generate_report()
    except Exception as e:
        logger.error(f"Error during agent analysis for portfolio {portfolio_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during compliance analysis: {e}")

    # === Ingest into Vector DB (RAG Service) ===
    try:
        # Convert report to JSON string for RAG ingestion
        report_json_string = json.dumps(report, indent=2)
        logger.info(f"Ingesting portfolio analysis into RAG service for {portfolio_id}...")
        ingest_portfolio_analysis(portfolio_id, report_json_string)
        logger.info(f"Successfully ingested analysis for portfolio {portfolio_id}.")
    except Exception as e:
        logger.error(f"Error ingesting analysis into RAG service for portfolio {portfolio_id}: {e}", exc_info=True)
        # Decide if this should be a critical error or if the process can continue without RAG
        raise HTTPException(status_code=500, detail=f"Error integrating with RAG service: {e}")

    # === Store in MongoDB ===
    portfolio_record = {
        "client_id": portfolio_data.get("client_id"),
        "portfolio_id": portfolio_id,
        "date": portfolio_data.get("date", datetime.utcnow().isoformat()),
        "positions": positions,
        "trades": portfolio_data.get("trades", []), # Keep existing trades if present
        "analysis": report,
        "uploaded_at": datetime.utcnow()
    }

    try:
        logger.info(f"Saving portfolio record to database for {portfolio_id}...")
        # Await is only effective if portfolio_collection is an async client (e.g., motor)
        await portfolio_collection.insert_one(portfolio_record)
        logger.info(f"Portfolio {portfolio_id} successfully saved to DB.")
    except Exception as e:
        logger.error(f"Error saving portfolio {portfolio_id} to database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error storing portfolio in database: {e}")

    return {
        "filename": file.filename,
        "analysis": report,
        "portfolio_id": portfolio_id,
        "status": "success"
    }

@app.get("/portfolios")
async def get_all_portfolios():
    """
    Retrieves a summary list of all uploaded portfolios, sorted by upload date.
    """
    logger.info("Fetching all portfolio summaries...")
    portfolios = []
    try:
        # Ensure portfolio_collection is async (motor) for await to be non-blocking
        cursor = portfolio_collection.find().sort("uploaded_at", -1)
        async for portfolio in cursor:
            serialized_portfolio = serialize_portfolio_summary(portfolio)
            if serialized_portfolio:
                portfolios.append(serialized_portfolio)
        logger.info(f"Found {len(portfolios)} portfolio summaries.")
        return portfolios
    except Exception as e:
        logger.error(f"Error fetching all portfolios: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolios: {e}")

@app.get("/portfolio/{id}")
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
    except HTTPException: # Re-raise FastAPI HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving portfolio {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio detail: {e}")

@app.post("/ask/{portfolio_id}")
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