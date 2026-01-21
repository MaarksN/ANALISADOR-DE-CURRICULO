import time
import random
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown

from src.modules.onboarding import OnboardingAgent
from src.modules.job_intelligence import JobScanner
from src.modules.profile_optimizer import ProfileOptimizer
from src.modules.resume_generator import ResumeGenerator
from src.modules.applier import ApplicationBot
from src.modules.interview_prep import InterviewCoach
from src.modules.decision_engine import StrategyEngine
from src.modules.monitoring import FollowUpAgent

console = Console()

class BirthHub360:
    def __init__(self):
        self.onboarding = OnboardingAgent()
        self.scanner = JobScanner()
        self.optimizer = ProfileOptimizer()
        self.resume_gen = ResumeGenerator()
        self.applier = ApplicationBot()
        self.coach = InterviewCoach()
        self.strategy_engine = StrategyEngine()
        self.monitoring = FollowUpAgent()

        self.profile = None
        self.metrics = {
            "scanned": 0,
            "matched": 0,
            "applied": 0,
            "interviews": 0,
            "followups": 0
        }
        self.last_strategy_update = "Inicializando..."
        self.interview_prep_status = "Nenhuma entrevista agendada."

    def start(self):
        self.profile = self.onboarding.load_default_profile()

        layout = self.make_layout()

        with Live(layout, refresh_per_second=4, screen=True):
            while True:
                # 1. Update Header
                layout["header"].update(Panel(Text("BIRTH HUB 360 AUTOMÁTICO - OPERANDO", style="bold green", justify="center")))

                # 2. Decision Engine Analysis
                strategy_msg = self.strategy_engine.analyze_performance(self.metrics, [])
                self.last_strategy_update = strategy_msg

                # 3. Scan
                layout["main"].update(Panel(Text("Escaneando oportunidades...", style="yellow")))
                time.sleep(1)

                keywords = [s.name for s in self.profile.skills]
                jobs = self.scanner.scan_opportunities(keywords)
                self.metrics["scanned"] += len(jobs)

                # 4. Match
                high_match_jobs = []
                for job in jobs:
                    score = self.scanner.calculate_match_score(self.profile, job)
                    if score > 50:
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

                # 5. Apply & Interview Simulation
                for job in high_match_jobs:
                    # Optimize
                    opt_profile = self.optimizer.optimize_for_job(self.profile, job)
                    # Resume
                    resume = self.resume_gen.generate_resume(opt_profile, job)
                    # Apply
                    app = self.applier.apply(opt_profile, job, resume)
                    self.metrics["applied"] += 1

                    # Update Log
                    layout["footer"].update(Panel(f"Candidatura enviada para {job.company} - {job.title} | Status: {app.status}"))

                    # SIMULATE INTERVIEW (10% chance for demo)
                    if random.random() < 0.1:
                        self.metrics["interviews"] += 1
                        questions = self.coach.generate_questions(job)
                        q_text = "\n".join([f"- {q}" for q in questions])
                        self.interview_prep_status = f"[bold]Preparação para {job.company}:[/bold]\n{q_text}\n\n[italic]Feedback IA:[/italic] {self.coach.simulate_feedback()}"

                        # Show interview prep in main temporarily
                        layout["main"].update(Panel(self.interview_prep_status, title="MÓDULO DE ENTREVISTAS ATIVO", style="bold white on blue"))
                        time.sleep(3) # Let user read

                    time.sleep(0.5)

                # 6. Monitoring & Follow-up
                follow_ups = self.monitoring.check_for_follow_up(self.applier.application_history)
                if follow_ups:
                    self.metrics["followups"] += len(follow_ups)
                    for action in follow_ups:
                         layout["footer"].update(Panel(f"[bold yellow]MONITORAMENTO:[/bold yellow] {action}"))
                         time.sleep(1)

                # Update Side Panel with Strategy & Metrics
                stats_text = f"""
                [bold]MÉTRICAS OPERACIONAIS[/bold]

                Escaneados: {self.metrics['scanned']}
                Compatíveis: {self.metrics['matched']}
                Candidaturas: {self.metrics['applied']}
                Entrevistas: {self.metrics['interviews']}
                Follow-ups: {self.metrics['followups']}

                [bold]Estratégia Ativa:[/bold]
                {self.strategy_engine.get_current_strategy()}
                [italic]{self.last_strategy_update}[/italic]

                [bold]Última Ação de IA:[/bold]
                Otimização de perfil para {high_match_jobs[-1].title if high_match_jobs else 'N/A'}
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
