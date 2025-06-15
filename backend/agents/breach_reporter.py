import logging

logger = logging.getLogger(__name__)

class BreachReporterAgent:
    def __init__(self, policy_violations: list, risk_drifts: list):
        if not isinstance(policy_violations, list):
            logger.warning(f"Expected policy_violations to be a list, but got {type(policy_violations)}")
            self.policy_violations = []
        else:
            self.policy_violations = policy_violations

        if not isinstance(risk_drifts, list):
            logger.warning(f"Expected risk_drifts to be a list, but got {type(risk_drifts)}")
            self.risk_drifts = []
        else:
            self.risk_drifts = risk_drifts
        logger.info("BreachReporterAgent initialized.")

    def generate_report(self) -> dict:
        report_summary = {}

        if self.policy_violations:
            report_summary["policy_violations_summary"] = (
                "The following policy violations were detected: " + "; ".join(self.policy_violations)
            )
            logger.info(f"Generated policy violations summary: {report_summary['policy_violations_summary']}")
        else:
            report_summary["policy_violations_summary"] = "No policy violations detected."
            logger.info("No policy violations detected.")

        if self.risk_drifts:

            risk_drift_summaries = [
                f"Risk drift in {d['sector']}: Actual {d['actual']:.2f}, Model {d['model']:.2f}, Drift {d['drift']:.2f} (Threshold: {d['threshold']:.2f})"
                for d in self.risk_drifts
            ]
            report_summary["risk_drifts_summary"] = (
                "Significant risk drifts were identified: " + "; ".join(risk_drift_summaries)
            )
            logger.info(f"Generated risk drifts summary: {report_summary['risk_drifts_summary']}")
        else:
            report_summary["risk_drifts_summary"] = "No significant risk drifts detected."
            logger.info("No significant risk drifts detected.")


        report_summary["raw_policy_violations"] = self.policy_violations
        report_summary["raw_risk_drifts"] = self.risk_drifts 

        logger.info("Breach report generated successfully.")
        return report_summary