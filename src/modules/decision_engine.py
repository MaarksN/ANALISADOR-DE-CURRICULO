from typing import Dict, List

class StrategyEngine:
    def __init__(self):
        self.current_strategy = "Aplicação Agressiva"
        self.focus_areas = ["Geral"]

    def analyze_performance(self, metrics: Dict[str, int], recent_applications: List[str]) -> str:
        """
        Analyzes metrics and returns a strategy update message.
        """
        conversion_rate = 0
        if metrics["applied"] > 0:
            conversion_rate = metrics["interviews"] / metrics["applied"]

        # Simple logic to switch strategies
        if conversion_rate < 0.1 and metrics["applied"] > 10:
            self.current_strategy = "Qualidade sobre Quantidade"
            return "Taxa de conversão baixa detectada. Mudando para foco em alta relevância."

        elif metrics["matched"] > 50 and metrics["applied"] < 10:
             self.current_strategy = "Sprint de Alto Volume"
             return "Muitos matches encontrados. Aumentando velocidade de aplicação."

        else:
            self.current_strategy = "Abordagem Equilibrada"
            return "Desempenho dentro dos parâmetros normais. Mantendo o curso."

    def get_current_strategy(self) -> str:
        return self.current_strategy
