from src.core.models import JobOpportunity, CandidateProfile
import random

class InterviewCoach:
    def __init__(self):
        self.common_questions = [
            "Fale um pouco sobre você.",
            "Por que você quer trabalhar na {company}?",
            "Qual é o seu maior ponto forte?",
            "Descreva uma situação desafiadora que você enfrentou."
        ]
        self.tech_questions_pool = [
            "Explique como você projetaria um sistema escalável para {topic}.",
            "Como você lida com dívida técnica?",
            "Qual é a sua experiência com {skill}?",
            "Descreva uma vez que você otimizou uma consulta lenta."
        ]

    def generate_questions(self, job: JobOpportunity) -> list[str]:
        """
        Generates a list of interview questions tailored to the job.
        """
        questions = []

        # Add a behavioral question customized to the company
        questions.append(random.choice(self.common_questions).format(company=job.company))

        # Add technical questions based on requirements
        for req in job.requirements[:2]: # Take first 2 requirements
            questions.append(f"Como você utilizou {req} em um ambiente de produção?")

        # Add a random system design or general tech question
        topic = job.title.split()[-1] if job.title else "software"
        questions.append(random.choice(self.tech_questions_pool).format(topic=topic, skill=random.choice(job.requirements) if job.requirements else "Python"))

        return questions

    def simulate_feedback(self) -> str:
        """
        Simulates feedback after a mock interview.
        """
        feedbacks = [
            "Boa comunicação. Elabore mais nos detalhes técnicos.",
            "Boa profundidade técnica. Tente ser mais conciso.",
            "Excelente fit cultural. Pronto para a entrevista real.",
            "Precisa de mais preparação em conceitos de design de sistemas."
        ]
        return random.choice(feedbacks)
