import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class ResumeImprover:
    def __init__(self):
        # Weighted keywords for better scoring
        self.keywords = {
            "Python": 5, "SQL": 4, "AWS": 5, "Docker": 4, "Kubernetes": 5,
            "API": 3, "REST": 3, "Git": 3, "CI/CD": 4, "Data Science": 5,
            "Machine Learning": 5, "Terraform": 5, "React": 3, "Node.js": 3
        }
        self.essential_sections = ["Experiência", "Educação", "Habilidades", "Projetos", "Resumo"]

    def analyze_resume(self, text):
        """Analyzes resume text using weighted scoring and section detection."""
        console.clear()
        console.print(Panel("[bold cyan]Analisador de Currículo Avançado (Hub de Vagas)[/bold cyan]", expand=False))

        # 1. Section Analysis
        found_sections = []
        missing_sections = []
        for section in self.essential_sections:
            if re.search(f"(?i){section}", text):
                found_sections.append(section)
            else:
                missing_sections.append(section)

        # 2. Keyword & Density Analysis
        score = 0
        max_score = sum(self.keywords.values())
        found_keywords = []
        missing_keywords = []

        for kw, weight in self.keywords.items():
            # Check for keyword existence (case insensitive)
            if re.search(f"(?i)\\b{re.escape(kw)}\\b", text):
                score += weight
                found_keywords.append(kw)
            else:
                missing_keywords.append(kw)

        # Normalize score to 100
        final_score = min(100, int((score / max_score) * 100))

        # Penalize for missing sections
        if missing_sections:
            final_score = max(0, final_score - (len(missing_sections) * 10))

        # --- DISPLAY RESULTS ---

        # Score Panel
        color = "green" if final_score >= 80 else "yellow" if final_score >= 50 else "red"
        console.print(Panel(f"[bold {color}]ATS Score: {final_score}/100[/bold {color}]", title="Pontuação de Compatibilidade"))

        # Sections Table
        table = Table(title="Estrutura do Currículo")
        table.add_column("Seção", style="cyan")
        table.add_column("Status", justify="center")

        for sec in self.essential_sections:
            status = "[green]Detectado[/green]" if sec in found_sections else "[red]Ausente[/red]"
            table.add_row(sec, status)
        console.print(table)

        # Keywords Analysis
        if found_keywords:
            console.print(f"\n[green]Competências Identificadas:[/green] {', '.join(found_keywords)}")

        if missing_keywords:
            console.print(f"\n[yellow]Oportunidades de Palavras-Chave (Tech Trending):[/yellow]")
            console.print(f"{', '.join(missing_keywords[:10])}")

        # Final Feedback
        feedback = []
        if final_score < 50:
            feedback.append("• Seu currículo está muito genérico. Adicione as palavras-chave listadas acima.")
        if missing_sections:
            feedback.append(f"• Estrutura incompleta. Adicione as seções: {', '.join(missing_sections)}.")
        if "Python" in found_keywords and "Git" not in found_keywords:
            feedback.append("• Dica: Desenvolvedores Python devem mencionar Git/Versionamento.")
        if not feedback:
            feedback.append("• Excelente currículo! Pronto para aplicação.")

        console.print(Panel("\n".join(feedback), title="Diagnóstico da IA", style="magenta"))
