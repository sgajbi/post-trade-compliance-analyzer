class BreachReporterAgent:
    def __init__(self, policy_violations, risk_drifts):
        self.policy_violations = policy_violations
        self.risk_drifts = risk_drifts

    def generate_report(self):
        return {
            "policy_violations": self.policy_violations,
            "risk_drifts": self.risk_drifts
        }
