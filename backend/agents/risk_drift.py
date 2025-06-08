import logging
from agents.config import MODEL_ALLOCATIONS, DRIFT_THRESHOLD # Import configurable values

logger = logging.getLogger(__name__)

class RiskDriftAgent:
    """
    Calculates sector weights for a portfolio and identifies significant drifts
    from predefined model allocations.
    """
    def __init__(self, positions: list):
        if not isinstance(positions, list):
            logger.warning(f"Expected positions to be a list, but got {type(positions)}")
            self.positions = []
        else:
            self.positions = positions

        self.model_allocations = MODEL_ALLOCATIONS # Loaded from config.py
        self.drift_threshold = DRIFT_THRESHOLD     # Loaded from config.py
        logger.info(f"RiskDriftAgent initialized with drift_threshold={self.drift_threshold}.")


    def run(self) -> list:
        """
        Calculates actual sector weights and identifies deviations from model allocations.
        """
        drifts = []
        
        # Filter and validate positions to ensure necessary data is present
        valid_positions = []
        for i, p in enumerate(self.positions):
            if not isinstance(p, dict):
                logger.warning(f"Invalid position data at index {i}: Expected dict, got {type(p)}. Skipping.")
                continue

            # Ensure 'quantity' and 'market_price' are present and numeric
            quantity = p.get("quantity")
            market_price = p.get("market_price")

            if (quantity is None or not isinstance(quantity, (int, float)) or
                market_price is None or not isinstance(market_price, (int, float))):
                symbol = p.get('symbol', 'N/A')
                drifts.append(f"Missing or invalid 'quantity' or 'market_price' for position '{symbol}' (index {i}).")
                logger.warning(f"Skipping position '{symbol}' (index {i}) due to missing/invalid quantity or market_price.")
                continue
            valid_positions.append(p)

        if not valid_positions:
            logger.info("No valid positions to calculate risk drift.")
            return ["Cannot calculate risk drift: No valid positions available."]

        # Calculate total portfolio value
        total_value = sum(p["quantity"] * p["market_price"] for p in valid_positions)

        if total_value == 0:
            logger.warning("Total portfolio value is zero. Cannot calculate sector weights.")
            return ["Cannot calculate risk drift: Total portfolio value is zero."]

        # Calculate actual sector weights
        sector_weights = {}
        for p in valid_positions:
            # Default to "Others" if sector is not provided in position data
            sector = p.get("sector", "Others")
            value = p["quantity"] * p["market_price"]
            sector_weights[sector] = sector_weights.get(sector, 0) + value

        # Normalize sector weights
        for sector in sector_weights:
            sector_weights[sector] /= total_value
        logger.info(f"Calculated actual sector weights: {sector_weights}")

        # Compare actual weights to model allocations
        for sector, actual_weight in sector_weights.items():
            model_weight = self.model_allocations.get(sector, 0.0) # Default to 0.0 if sector not in model_allocations
            drift = abs(actual_weight - model_weight)

            if drift > self.drift_threshold:
                drift_message = (
                    f"Risk drift in {sector}: Actual {actual_weight:.2f}, "
                    f"Model {model_weight:.2f}, Drift {drift:.2f} (Threshold: {self.drift_threshold})"
                )
                drifts.append(drift_message)
                logger.info(f"Risk drift detected: {drift_message}")
        
        # Check for sectors in model_allocations that are not present in actual portfolio
        for model_sector, model_weight in self.model_allocations.items():
            if model_sector not in sector_weights and model_weight > 0: # If a model sector is missing but has target weight
                drift = abs(0 - model_weight) # Actual weight is 0
                if drift > self.drift_threshold:
                    drift_message = (
                        f"Missing sector in portfolio (present in model): {model_sector}. "
                        f"Actual 0.00, Model {model_weight:.2f}, Drift {drift:.2f} (Threshold: {self.drift_threshold})"
                    )
                    drifts.append(drift_message)
                    logger.info(f"Risk drift detected (missing sector): {drift_message}")

        logger.info(f"Finished risk drift analysis. Found {len(drifts)} drifts.")
        return drifts