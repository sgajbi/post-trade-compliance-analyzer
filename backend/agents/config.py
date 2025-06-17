# Model allocations for risk drift analysis
MODEL_ALLOCATIONS = {
    "Technology": 0.4,
    "Consumer Discretionary": 0.2,
    "Others": 0.4
}

# Threshold for detecting significant risk drifts (e.g., 0.1 for 10%)
DRIFT_THRESHOLD = 0.1

# Policy rules for policy validation (example - can be extended)
# For more complex rules, consider a more structured format or a dedicated rules engine
POLICY_RULES = [
    {"sector": "Technology", "quantity_gt": 90, "violation_message": "Overweight in Technology"}
]

"""
POLICY_RULES = [
    {"sector": "Technology", "quantity_gt": 90, "violation_message": "Overweight in Technology"},

    # Sector-based rules
    {"sector": "Consumer Discretionary", "quantity_gt": 70, "violation_message": "Overweight in Consumer Discretionary"},
    {"sector": "Energy", "quantity_gt": 50, "violation_message": "Overweight in Energy"},
    {"sector": "Financials", "quantity_gt": 60, "violation_message": "Overweight in Financials"},

    # Minimum diversification requirement (e.g., must hold at least 3 sectors)
    {"min_sector_count": 3, "violation_message": "Insufficient sector diversification"},

    # Asset class rules (assuming your position data includes asset_class)
    {"asset_class": "Equity", "weight_gt": 0.8, "violation_message": "Equity overweight - too risky"},
    {"asset_class": "Fixed Income", "weight_lt": 0.1, "violation_message": "Fixed Income underweight - lack of stability"},

    # ESG rule
    {"esg_rating_lt": 3, "violation_message": "Position violates ESG threshold"},

    # Country/region exposure (assuming you track region)
    {"region": "Emerging Markets", "weight_gt": 0.3, "violation_message": "Overexposure to Emerging Markets"},

    # Single instrument concentration (e.g., Apple makes up 25% of portfolio)
    {"instrument": "AAPL", "weight_gt": 0.25, "violation_message": "Single instrument overweight - AAPL concentration"}
]
"""