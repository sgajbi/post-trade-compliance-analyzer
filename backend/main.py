import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from agents.policy_validator import PolicyValidatorAgent
from agents.risk_drift import RiskDriftAgent
from agents.breach_reporter import BreachReporterAgent

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

    # Agent 1
    policy_agent = PolicyValidatorAgent(positions)
    policy_violations = policy_agent.run()

    # Agent 2
    drift_agent = RiskDriftAgent(positions)
    risk_drifts = drift_agent.run()

    # Agent 3
    reporter = BreachReporterAgent(policy_violations, risk_drifts)
    report = reporter.generate_report()

    return {
        "filename": file.filename,
        "analysis": report
    }
