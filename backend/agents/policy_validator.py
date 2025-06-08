import logging

logger = logging.getLogger(__name__)

class PolicyValidatorAgent:
    """
    Validates investment positions against predefined policy rules.
    Currently checks for overweight in Technology sector.
    """
    def __init__(self, positions: list):
        if not isinstance(positions, list):
            logger.warning(f"Expected positions to be a list, but got {type(positions)}")
            self.positions = []
        else:
            self.positions = positions
        logger.info("PolicyValidatorAgent initialized.")

    def run(self) -> list:
        """
        Executes policy validation rules against the provided positions.
        """
        violations = []
        logger.info(f"Starting policy validation for {len(self.positions)} positions.")

        for i, pos in enumerate(self.positions):
            if not isinstance(pos, dict):
                violations.append(f"Invalid position data at index {i}: Expected dict, got {type(pos)}")
                logger.warning(f"Skipping invalid position data at index {i}: {pos}")
                continue

            sector = pos.get("sector")
            quantity = pos.get("quantity")
            symbol = pos.get("symbol", "N/A") # Default symbol if not found

            # Check for critical missing data
            if sector is None or quantity is None:
                violations.append(f"Missing 'sector' or 'quantity' for position '{symbol}' (index {i}).")
                logger.warning(f"Missing critical data for position '{symbol}' at index {i}. Skipping policy check for this position.")
                continue

            # Policy Rule 1: Overweight in Technology
            # This rule is hardcoded. For more flexibility, consider externalizing rules.
            if sector == "Technology" and quantity > 90:
                violation_message = f"Overweight in Technology: {symbol} (Quantity: {quantity})"
                violations.append(violation_message)
                logger.info(f"Policy violation detected: {violation_message}")

            # Add more policy rules here as needed
            # Example: if pos.get("risk_category") == "High" and pos.get("value") > 100000:
            #     violations.append(f"High-value, high-risk asset: {symbol}")

        logger.info(f"Finished policy validation. Found {len(violations)} violations.")
        return violations