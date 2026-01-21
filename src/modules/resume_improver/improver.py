from rich.console import Console
from rich.panel import Panel

console = Console()

class ResumeImprover:
    def __init__(self):
        self.keywords = ["Python", "SQL", "Cloud", "AWS", "Docker", "Kubernetes", "API", "REST", "Git", "CI/CD"]

    def analyze_resume(self, text):
        """Analyzes resume text and suggests improvements."""
        console.clear()
        console.print(Panel("[bold cyan]Analisador de Currículo com IA[/bold cyan]", expand=False))

        score = 0
        missing = []
        found = []

        # Simple keyword matching simulation
        for kw in self.keywords:
            if kw.lower() in text.lower():
                score += 10
                found.append(kw)
            else:
                missing.append(kw)

        # Display results
        console.print(f"\n[bold]Pontuação Calculada:[/bold] {score}/100\n")

        if found:
            console.print(f"[green]Pontos Fortes Detectados:[/green] {', '.join(found)}")

        if missing:
            console.print(f"\n[yellow]Sugestões de Melhoria:[/yellow]")
            console.print("Considere adicionar experiência ou projetos relacionados a:")
            for m in missing:
                console.print(f"- [bold]{m}[/bold]")

        suggestion = ""
        if score < 50:
            suggestion = "Seu currículo precisa de mais palavras-chave técnicas para passar nos filtros ATS."
        elif score < 80:
            suggestion = "Bom currículo! Tente quantificar seus resultados (ex: 'melhorou performance em 20%')."
        else:
            suggestion = "Excelente! Seu perfil está muito competitivo."

        console.print(Panel(suggestion, title="Feedback da IA", style="magenta"))
