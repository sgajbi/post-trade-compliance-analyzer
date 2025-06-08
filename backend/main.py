import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

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

    # === AGENT 1: Policy Validator ===
    policy_violations = []
    for pos in positions:
        if pos["sector"] == "Technology" and pos["quantity"] > 90:
            policy_violations.append(f"Overweight in Technology: {pos['symbol']}")

    # === AGENT 2: Risk Drift ===
    model_allocations = {
        "Technology": 0.4,
        "Consumer Discretionary": 0.2,
        "Others": 0.4
    }

    total_value = sum(p["quantity"] * p["market_price"] for p in positions)
    sector_weights = {}
    for p in positions:
        sector = p["sector"]
        value = p["quantity"] * p["market_price"]
        sector_weights[sector] = sector_weights.get(sector, 0) + value

    for sector in sector_weights:
        sector_weights[sector] /= total_value

    drift_alerts = []
    for sector, weight in sector_weights.items():
        model_weight = model_allocations.get(sector, 0)
        if abs(weight - model_weight) > 0.1:  # 10% tolerance
            drift_alerts.append(f"Risk drift in {sector}: Actual {weight:.2f}, Model {model_weight:.2f}")

    # === AGENT 3: Breach Reporter ===
    report = {
        "policy_violations": policy_violations,
        "risk_drifts": drift_alerts
    }

    return {
        "filename": file.filename,
        "analysis": report
    }