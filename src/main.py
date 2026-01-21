import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text

from src.modules.onboarding import OnboardingAgent
from src.modules.job_intelligence import JobScanner
from src.modules.profile_optimizer import ProfileOptimizer
from src.modules.resume_generator import ResumeGenerator
from src.modules.applier import ApplicationBot

console = Console()

class BirthHub360:
    def __init__(self):
        self.onboarding = OnboardingAgent()
        self.scanner = JobScanner()
        self.optimizer = ProfileOptimizer()
        self.resume_gen = ResumeGenerator()
        self.applier = ApplicationBot()
        self.profile = None
        self.metrics = {
            "scanned": 0,
            "matched": 0,
            "applied": 0,
            "interviews": 0
        }

    def start(self):
        self.profile = self.onboarding.load_default_profile()

        layout = self.make_layout()

        with Live(layout, refresh_per_second=4, screen=True):
            while True: # In a real app this runs forever. For demo we might want to break or just let it run.
                # 1. Update Header
                layout["header"].update(Panel(Text("BIRTH HUB 360 AUTOMÁTICO - OPERANDO", style="bold green", justify="center")))

                # 2. Scan
                layout["main"].update(Panel(Text("Escaneando oportunidades...", style="yellow")))
                time.sleep(1)

                keywords = [s.name for s in self.profile.skills]
                jobs = self.scanner.scan_opportunities(keywords)
                self.metrics["scanned"] += len(jobs)

                # 3. Match & Apply
                high_match_jobs = []
                for job in jobs:
                    score = self.scanner.calculate_match_score(self.profile, job)
                    if score > 50: # Threshold
                        high_match_jobs.append(job)
                        job.match_score = score

                self.metrics["matched"] += len(high_match_jobs)

                # Display Jobs
                job_table = Table(title="Oportunidades Recentes")
                job_table.add_column("Empresa", style="cyan")
                job_table.add_column("Cargo", style="magenta")
                job_table.add_column("Match %", justify="right")

                for job in high_match_jobs[-5:]:
                    job_table.add_row(job.company, job.title, f"{job.match_score:.1f}%")

                layout["main"].update(Panel(job_table))
                time.sleep(1)

                # 4. Apply Loop
                for job in high_match_jobs:
                    # Optimize Profile (Internal simulation)
                    opt_profile = self.optimizer.optimize_for_job(self.profile, job)

                    # Generate Resume
                    resume = self.resume_gen.generate_resume(opt_profile, job)

                    # Apply
                    app = self.applier.apply(opt_profile, job, resume)
                    self.metrics["applied"] += 1

                    # Update Log
                    layout["footer"].update(Panel(f"Candidatura enviada para {job.company} - {job.title} | Status: {app.status}"))
                    time.sleep(0.5) # Simulate work

                # Update Metrics Side Panel
                stats_text = f"""
                [bold]MÉTRICAS OPERACIONAIS[/bold]

                Escaneados: {self.metrics['scanned']}
                Compatíveis: {self.metrics['matched']}
                Candidaturas: {self.metrics['applied']}
                Entrevistas: {self.metrics['interviews']} (Aguardando)

                [bold]Estratégia Ativa:[/bold]
                Aplicação Agressiva
                Foco: Python, Cloud
                """
                layout["side"].update(Panel(stats_text))

                # Pause before next cycle
                time.sleep(2)

    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["body"].split_row(
            Layout(name="side", ratio=1),
            Layout(name="main", ratio=3)
        )
        return layout

if __name__ == "__main__":
    try:
        hub = BirthHub360()
        hub.start()
    except KeyboardInterrupt:
        console.print("[bold red]Sistema Encerrado.[/bold red]")
