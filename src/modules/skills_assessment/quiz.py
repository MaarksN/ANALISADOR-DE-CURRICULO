from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

class SkillsQuiz:
    def __init__(self):
        self.quizzes = {
            "Python": [
                {"q": "Qual é a saída de print(2 ** 3)?", "options": ["5", "6", "8", "9"], "a": "3"},
                {"q": "Qual método adiciona um item ao final de uma lista?", "options": ["push()", "add()", "append()", "insert()"], "a": "3"},
                {"q": "O que é um decorador?", "options": ["Uma classe", "Uma função que modifica outra", "Um comentário", "Um erro"], "a": "2"}
            ],
            "SQL": [
                {"q": "Qual comando é usado para buscar dados?", "options": ["GET", "OPEN", "SELECT", "FETCH"], "a": "3"},
                {"q": "Qual cláusula filtra registros?", "options": ["WHERE", "FILTER", "LIMIT", "GROUP"], "a": "1"},
                {"q": "Como remover duplicatas?", "options": ["UNIQUE", "DISTINCT", "DIFFERENT", "REMOVE"], "a": "2"}
            ]
        }

    def run_quiz(self):
        console.clear()
        console.print(Panel("[bold cyan]Avaliação Técnica - Hub de Vagas[/bold cyan]", expand=False))

        topic = Prompt.ask("Escolha o tema", choices=list(self.quizzes.keys()), default="Python")
        questions = self.quizzes[topic]
        score = 0

        for i, item in enumerate(questions, 1):
            console.print(f"\n[bold yellow]{i}. {item['q']}[/bold yellow]")
            for idx, opt in enumerate(item['options'], 1):
                console.print(f"{idx}) {opt}")

            answer = Prompt.ask("Sua resposta", choices=["1", "2", "3", "4"])
            if answer == item['a']:
                console.print("[green]Correto![/green]")
                score += 1
            else:
                correct_text = item['options'][int(item['a'])-1]
                console.print(f"[red]Incorreto. A resposta certa era: {correct_text}[/red]")

        final_score = int((score / len(questions)) * 100)
        color = "green" if final_score >= 70 else "red"
        console.print(Panel(f"Pontuação Final: [bold {color}]{final_score}%[/bold {color}]", title="Resultado"))
