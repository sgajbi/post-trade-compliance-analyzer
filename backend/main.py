import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from agents.policy_validator import PolicyValidatorAgent
from agents.risk_drift import RiskDriftAgent
from agents.breach_reporter import BreachReporterAgent
from db.mongo import portfolio_collection
from datetime import datetime
from fastapi import HTTPException
from bson import ObjectId
from rag_service import ingest_portfolio_analysis
from rag_service import query_portfolio



app = FastAPI()

origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def serialize_portfolio_summary(portfolio):
    return {
        "id": str(portfolio["_id"]),
        "client_id": portfolio.get("client_id"),
        "portfolio_id": portfolio.get("portfolio_id"),
        "date": portfolio.get("date"),
        "uploaded_at": portfolio.get("uploaded_at")
    }

def serialize_portfolio_detail(portfolio):
    portfolio["id"] = str(portfolio["_id"])
    del portfolio["_id"]
    return portfolio

@app.get("/")
def read_root():
    return {"message": "Post-Trade Compliance Analyzer backend is running"}

@app.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    contents = await file.read()
    decoded = contents.decode("utf-8")
    portfolio = json.loads(decoded)

    positions = portfolio.get("positions", [])

    # === Agents ===
    policy_violations = PolicyValidatorAgent(positions).run()
    risk_drifts = RiskDriftAgent(positions).run()
    report = BreachReporterAgent(policy_violations, risk_drifts).generate_report()

    # Ingest into vector DB
    ingest_portfolio_analysis(portfolio.get("portfolio_id"), json.dumps(report, indent=2))


    # === Store in DB ===
    portfolio_record = {
        "client_id": portfolio.get("client_id"),
        "portfolio_id": portfolio.get("portfolio_id"),
        "date": portfolio.get("date", datetime.utcnow().isoformat()),
        "positions": positions,
        "trades": portfolio.get("trades", []),
        "analysis": report,
        "uploaded_at": datetime.utcnow()
    }

    await portfolio_collection.insert_one(portfolio_record)

    return {
        "filename": file.filename,
        "analysis": report,
        "status": "saved_to_db"
    }

@app.get("/portfolios")
async def get_all_portfolios():
    cursor = portfolio_collection.find().sort("uploaded_at", -1)
    portfolios = []
    async for portfolio in cursor:
        portfolios.append(serialize_portfolio_summary(portfolio))
    return portfolios

@app.get("/portfolio/{id}")
async def get_portfolio(id: str):
    try:
        portfolio = await portfolio_collection.find_one({"_id": ObjectId(id)})
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return serialize_portfolio_detail(portfolio)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


@app.post("/ask/{portfolio_id}")
async def ask_question(portfolio_id: str, question: str):
    try:
        answer = query_portfolio(portfolio_id, question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))