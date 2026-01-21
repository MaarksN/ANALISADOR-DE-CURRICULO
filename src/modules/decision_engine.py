from typing import Dict, List

class StrategyEngine:
    def __init__(self):
        self.current_strategy = "Aggressive Application"
        self.focus_areas = ["General"]

    def analyze_performance(self, metrics: Dict[str, int], recent_applications: List[str]) -> str:
        """
        Analyzes metrics and returns a strategy update message.
        """
        conversion_rate = 0
        if metrics["applied"] > 0:
            conversion_rate = metrics["interviews"] / metrics["applied"]

        # Simple logic to switch strategies
        if conversion_rate < 0.1 and metrics["applied"] > 10:
            self.current_strategy = "Quality over Quantity"
            return "Low conversion rate detected. Switching to high-relevance targeting."

        elif metrics["matched"] > 50 and metrics["applied"] < 10:
             self.current_strategy = "High Volume Sprint"
             return "Many matches found. Increasing application velocity."

        else:
            self.current_strategy = "Balanced Approach"
            return "Performance within normal parameters. Maintaining course."

    def get_current_strategy(self) -> str:
        return self.current_strategy
