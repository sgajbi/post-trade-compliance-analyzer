class RiskDriftAgent:
    def __init__(self, positions):
        self.positions = positions
        self.model_allocations = {
            "Technology": 0.4,
            "Consumer Discretionary": 0.2,
            "Others": 0.4
        }

    def run(self):
        total_value = sum(p["quantity"] * p["market_price"] for p in self.positions)
        sector_weights = {}
        for p in self.positions:
            sector = p["sector"]
            value = p["quantity"] * p["market_price"]
            sector_weights[sector] = sector_weights.get(sector, 0) + value

        for sector in sector_weights:
            sector_weights[sector] /= total_value

        drifts = []
        for sector, weight in sector_weights.items():
            model_weight = self.model_allocations.get(sector, 0)
            if abs(weight - model_weight) > 0.1:
                drifts.append(f"Risk drift in {sector}: Actual {weight:.2f}, Model {model_weight:.2f}")
        return drifts
