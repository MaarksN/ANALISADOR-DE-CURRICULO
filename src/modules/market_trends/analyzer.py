import random
from rich.console import Console
from rich.table import Table

console = Console()

class MarketAnalyzer:
    def __init__(self):
        self.trending_skills = {
            "IA Generativa": 98,
            "Python": 95,
            "Cloud Computing": 92,
            "Data Engineering": 88,
            "DevSecOps": 85
        }
        self.hot_roles = [
            "Engenheiro de IA",
            "Arquiteto de Soluções",
            "Engenheiro de Dados Sênior",
            "Desenvolvedor Full Stack (Python/React)"
        ]

    def show_trends(self):
        """Displays simulated market trends."""
        console.clear()
        console.print("[bold cyan]Análise de Tendências de Mercado[/bold cyan]\n")

        # Skills Table
        table = Table(title="Habilidades em Alta (Últimos 30 dias)")
        table.add_column("Habilidade", style="green")
        table.add_column("Índice de Demanda", justify="right", style="magenta")

        for skill, score in self.trending_skills.items():
            # Simulate slight fluctuation
            current_score = min(100, score + random.randint(-2, 2))
            table.add_row(skill, f"{current_score}/100")

        console.print(table)

        # Roles
        console.print("\n[bold yellow]Cargos com Maior Volume de Vagas:[/bold yellow]")
        for role in self.hot_roles:
            console.print(f"- {role}")

        console.print("\n[italic]Dados baseados em análise simulada de agregadores de vagas.[/italic]")
