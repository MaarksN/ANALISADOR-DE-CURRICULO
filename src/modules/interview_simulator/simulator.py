import time
import random
from rich.panel import Panel
from rich.console import Console
from rich.prompt import Prompt

console = Console()

class InterviewSimulator:
    def __init__(self):
        self.questions_db = [
            "Fale um pouco sobre você.",
            "Por que você quer trabalhar nesta empresa?",
            "Qual foi seu maior desafio técnico até hoje?",
            "Como você lida com prazos apertados?",
            "Onde você se vê daqui a 5 anos?"
        ]

    def run_session(self):
        """Runs an interactive interview session in the terminal."""
        console.clear()
        console.print(Panel("[bold cyan]Simulador de Entrevista - Hub de Vagas[/bold cyan]", expand=False))
        console.print("O sistema fará perguntas e avaliará suas respostas (Simulado).\n")

        questions = random.sample(self.questions_db, 3)
        history = []

        for i, q in enumerate(questions, 1):
            console.print(f"[bold yellow]Pergunta {i}:[/bold yellow] {q}")
            answer = Prompt.ask("[italic]Sua resposta[/italic]")

            # Mock analysis simulation
            with console.status("[bold green]Analisando resposta...[/bold green]", spinner="dots"):
                time.sleep(1.5)

            feedback = self._generate_feedback(answer)
            console.print(f"[bold magenta]Feedback da IA:[/bold magenta] {feedback}\n")
            history.append({"q": q, "a": answer, "f": feedback})
            time.sleep(1)

        console.print(Panel("[bold green]Sessão Finalizada![/bold green] Resumo salvo no histórico."))
        return history

    def _generate_feedback(self, answer):
        """Generates simple mock feedback based on answer length."""
        if len(answer) < 20:
            return "Sua resposta foi muito curta. Tente elaborar mais sobre suas experiências usando o método STAR."
        elif len(answer) > 200:
            return "Boa profundidade, mas cuidado para não ser prolixo. Tente ser mais direto."
        else:
            return "Resposta equilibrada. Bons pontos levantados."
