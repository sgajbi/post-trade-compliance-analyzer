class PolicyValidatorAgent:
    def __init__(self, positions):
        self.positions = positions

    def run(self):
        violations = []
        for pos in self.positions:
            if pos["sector"] == "Technology" and pos["quantity"] > 90:
                violations.append(f"Overweight in Technology: {pos['symbol']}")
        return violations
