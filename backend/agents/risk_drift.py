"""
This Python code defines a class RiskDriftAgent that analyzes sector allocation drifts 
in a portfolio by comparing the actual sector weights with predefined model allocations, 
and flags significant deviations (drifts) that exceed a configured threshold.
"""
import logging
from agents.config import MODEL_ALLOCATIONS, DRIFT_THRESHOLD

logger = logging.getLogger(__name__)

class RiskDriftAgent:
    def __init__(self, positions: list):
        if not isinstance(positions, list):
            logger.warning(f"Expected positions to be a list, but got {type(positions)}")
            self.positions = []
        else:
            self.positions = positions

        self.model_allocations = MODEL_ALLOCATIONS
        self.drift_threshold = DRIFT_THRESHOLD
        logger.info(f"RiskDriftAgent initialized with drift_threshold={self.drift_threshold}.")

    def run(self) -> list:
        drifts = []

        valid_positions = []
        for i, p in enumerate(self.positions):
            if not isinstance(p, dict):
                logger.warning(f"Invalid position data at index {i}: Expected dict, got {type(p)}. Skipping.")
                continue
            quantity = p.get("quantity")
            market_price = p.get("market_price")
            if not isinstance(quantity, (int, float)) or not isinstance(market_price, (int, float)):
                logger.warning(f"Missing or invalid 'quantity' or 'market_price' for position at index {i}. Skipping.")
                continue
            valid_positions.append(p)

        if not valid_positions:
            logger.info("No valid positions found for risk drift analysis.")
            return []

        total_value = sum(p["quantity"] * p["market_price"] for p in valid_positions)
        if total_value == 0:
            logger.warning("Total portfolio value is zero. Cannot calculate sector weights.")
            return []

        sector_weights = {}
        for p in valid_positions:
            sector = p.get("sector", "Unknown")
            value = p["quantity"] * p["market_price"]
            sector_weights[sector] = sector_weights.get(sector, 0) + value

        for sector in sector_weights:
            sector_weights[sector] /= total_value

        logger.info(f"Calculated actual sector weights: {sector_weights}")

        for sector, actual_weight in sector_weights.items():
            model_weight = self.model_allocations.get(sector, 0.0)
            drift = abs(actual_weight - model_weight)

            if drift > self.drift_threshold:
                drifts.append({
                    "sector": sector,
                    "actual": actual_weight,
                    "model": model_weight,
                    "drift": drift,
                    "threshold": self.drift_threshold
                })
                logger.info(f"Risk drift detected: Risk drift in {sector}: Actual {actual_weight:.2f}, Model {model_weight:.2f}, Drift {drift:.2f} (Threshold: {self.drift_threshold})")

        for model_sector, model_weight in self.model_allocations.items():
            if model_sector not in sector_weights and model_weight > 0:
                drift = abs(0 - model_weight)
                if drift > self.drift_threshold:
                    drifts.append({
                        "sector": model_sector,
                        "actual": 0.0,
                        "model": model_weight,
                        "drift": drift,
                        "threshold": self.drift_threshold
                    })
                    logger.info(f"Risk drift detected (missing sector): Missing sector in portfolio (present in model): {model_sector}. Actual 0.00, Model {model_weight:.2f}, Drift {drift:.2f} (Threshold: {self.drift_threshold})")

        logger.info(f"Finished risk drift analysis. Found {len(drifts)} drifts.")
        return drifts