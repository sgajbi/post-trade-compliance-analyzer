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