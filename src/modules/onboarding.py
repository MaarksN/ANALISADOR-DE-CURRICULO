from src.core.models import CandidateProfile, Experience, Education, Skill
from datetime import date
from faker import Faker
import random

fake = Faker('pt_BR')

class OnboardingAgent:
    def __init__(self):
        self.profile = None

    def load_default_profile(self) -> CandidateProfile:
        """Loads a hardcoded default profile for demonstration in PT-BR."""
        self.profile = CandidateProfile(
            name="Alex Desenvolvedor",
            email="alex.dev@exemplo.com.br",
            phone="+55 11 99999-9999",
            summary="Engenheiro de Software Sênior com 8 anos de experiência em Python e Arquiteturas em Nuvem.",
            experiences=[
                Experience(
                    title="Engenheiro Backend Sênior",
                    company="TechCorp Brasil",
                    start_date=date(2020, 1, 15),
                    description="Liderando migração de microsserviços e otimizando consultas de banco de dados."
                ),
                Experience(
                    title="Desenvolvedor de Software",
                    company="Inova Startup",
                    start_date=date(2016, 6, 1),
                    end_date=date(2019, 12, 31),
                    description="Desenvolvimento Full stack usando Django e React."
                )
            ],
            education=[
                Education(
                    institution="Universidade Tecnológica",
                    degree="Bacharelado",
                    field_of_study="Ciência da Computação",
                    start_date=date(2012, 8, 1),
                    end_date=date(2016, 5, 20)
                )
            ],
            skills=[
                Skill(name="Python", level="Especialista"),
                Skill(name="Docker", level="Intermediário"),
                Skill(name="AWS", level="Avançado")
            ],
            linkedin_url="https://linkedin.com/in/alexdev"
        )
        return self.profile

    def create_fake_profile(self) -> CandidateProfile:
        """Generates a random fake profile."""
        self.profile = CandidateProfile(
            name=fake.name(),
            email=fake.email(),
            phone=fake.phone_number(),
            summary=fake.text(),
            experiences=[
                Experience(
                    title=fake.job(),
                    company=fake.company(),
                    start_date=fake.date_between(start_date='-5y', end_date='-1y'),
                    description=fake.text()
                )
            ],
            education=[
                Education(
                    institution=fake.company(),
                    degree="Bacharelado",
                    field_of_study="Ciência da Computação",
                    start_date=fake.date_between(start_date='-10y', end_date='-6y'),
                    end_date=fake.date_between(start_date='-6y', end_date='-5y')
                )
            ],
            skills=[Skill(name=fake.word(), level="Intermediário") for _ in range(3)]
        )
        return self.profile
