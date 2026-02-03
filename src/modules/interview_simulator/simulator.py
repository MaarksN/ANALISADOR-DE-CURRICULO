import time
import random
from rich.panel import Panel
from rich.console import Console
from rich.prompt import Prompt
from src.core.llm import LLMClient

console = Console()

class InterviewSimulator:
    def __init__(self):
        self.llm = LLMClient()
        self.questions_db = {
            "Junior": [
                "O que é uma lista em Python?",
                "Como você aprende novas tecnologias?",
                "Explique o conceito de API REST.",
                "Qual a diferença entre SQL e NoSQL?"
            ],
            "Pleno": [
                "Como você lidaria com um bug em produção?",
                "Explique o ciclo de vida de uma thread.",
                "Quais os benefícios de usar Docker?",
                "Descreva sua experiência com CI/CD."
            ],
            "Senior": [
                "Desenhe uma arquitetura escalável para milhões de usuários.",
                "Como você mentora desenvolvedores mais júnior?",
                "Explique o Teorema CAP.",
                "Como você decide entre Monolito e Microsserviços?"
            ]
        }

    def run_session(self):
        """Runs an interactive interview session in the terminal."""
        console.clear()
        console.print(Panel("[bold cyan]Simulador de Entrevista Pro - Hub de Vagas[/bold cyan]", expand=False))

        # Difficulty Selection
        console.print("\n[bold]Selecione o Nível da Entrevista:[/bold]")
        console.print("1. Junior")
        console.print("2. Pleno")
        console.print("3. Senior")
        choice = Prompt.ask("Opção", choices=["1", "2", "3"], default="2")

        level_map = {"1": "Junior", "2": "Pleno", "3": "Senior"}
        level = level_map[choice]

        console.print(f"\n[green]Iniciando simulação nível {level}...[/green]\n")

        questions = random.sample(self.questions_db[level], 3)
        history = []

        for i, q in enumerate(questions, 1):
            console.print(f"[bold yellow]Pergunta {i}:[/bold yellow] {q}")
            answer = Prompt.ask("[italic]Sua resposta[/italic]")

            # Mock analysis simulation
            with console.status("[bold green]Analisando resposta (NLP)...[/bold green]", spinner="dots"):
                time.sleep(1.5)

            feedback = self._generate_feedback(answer, level)
            console.print(f"[bold magenta]Feedback da IA:[/bold magenta] {feedback}\n")
            history.append({"q": q, "a": answer, "f": feedback})
            time.sleep(1)

        console.print(Panel("[bold green]Sessão Finalizada![/bold green] Otimize suas respostas e tente novamente."))
        return history

    def _generate_feedback(self, answer, level):
        """Generates feedback using LLM if available, otherwise mock logic."""
        if self.llm.is_active():
            prompt = f"Avalie a seguinte resposta de um candidato para uma vaga nível {level}. Seja construtivo e breve.\nResposta: {answer}"
            feedback = self.llm.generate_response(prompt, system_role="Você é um recrutador técnico experiente.")
            if feedback: return feedback

        # Fallback Logic
        word_count = len(answer.split())

        if word_count < 10:
            return "Muito superficial. Em uma entrevista técnica, detalhe o 'como' e o 'porquê'."

        if level == "Senior" and word_count < 30:
            return "Para nível Sênior, espera-se uma visão mais arquitetural e detalhada. Aprofunde."

        if "depende" in answer.lower() and level == "Senior":
            return "Ótimo uso do 'depende'. Seniores sabem que não há bala de prata."

        if word_count > 100:
            return "Resposta detalhada, muito bom. Tente manter o foco para não divagar."

        return "Boa resposta. Demonstrou conhecimento do fundamento."
