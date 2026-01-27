from rich.console import Console
from rich.panel import Panel

console = Console()

class SalaryAdvisor:
    def __init__(self):
        # Mock database of salary ranges (BRL)
        self.salary_db = {
            "junior": {"min": 3000, "max": 5000},
            "pleno": {"min": 6000, "max": 9000},
            "senior": {"min": 10000, "max": 16000},
            "tech_lead": {"min": 18000, "max": 25000}
        }

    def advise(self, role, level):
        console.clear()
        console.print(Panel("[bold cyan]Consultor de Negociação Salarial[/bold cyan]", expand=False))

        level_key = level.lower()
        if level_key not in self.salary_db:
            level_key = "pleno" # Default

        data = self.salary_db[level_key]
        avg = (data["min"] + data["max"]) / 2

        console.print(f"\n[bold]Cargo:[/bold] {role} ({level})")
        console.print(f"[bold]Faixa Estimada (BR):[/bold] R$ {data['min']} - R$ {data['max']}")
        console.print(f"[bold]Média de Mercado:[/bold] R$ {avg}\n")

        console.print("[bold yellow]Estratégia de Negociação:[/bold yellow]")
        console.print("1. Nunca diga um número primeiro. Pergunte o budget da vaga.")
        console.print(f"2. Se pressionado, dê um intervalo: 'Estou buscando algo entre R$ {int(avg)} e R$ {data['max']}'.")
        console.print("3. Valorize benefícios (PLR, Saúde, Remoto) como parte do pacote total.")
        console.print("4. Pesquise a empresa no Glassdoor antes da reunião.")

        console.print(Panel("Lembre-se: O 'não' você já tem. Negocie com confiança baseada em dados.", style="green"))
