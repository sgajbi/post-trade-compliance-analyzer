import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from agents.policy_validator import PolicyValidatorAgent
from agents.risk_drift import RiskDriftAgent
from agents.breach_reporter import BreachReporterAgent
from db.mongo import portfolio_collection
from datetime import datetime


app = FastAPI()

origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
