from src.core.models import CandidateProfile, Experience, Education, Skill
from datetime import date
from faker import Faker
import random

fake = Faker()

class OnboardingAgent:
    def __init__(self):
        self.profile = None

    def load_default_profile(self) -> CandidateProfile:
        """Loads a hardcoded default profile for demonstration."""
        self.profile = CandidateProfile(
            name="Alex Developer",
            email="alex.dev@example.com",
            phone="+55 11 99999-9999",
            summary="Senior Software Engineer with 8 years of experience in Python and Cloud Architectures.",
            experiences=[
                Experience(
                    title="Senior Backend Engineer",
                    company="TechCorp",
                    start_date=date(2020, 1, 15),
                    description="Leading microservices migration and optimizing database queries."
                ),
                Experience(
                    title="Software Developer",
                    company="StartUp Inc",
                    start_date=date(2016, 6, 1),
                    end_date=date(2019, 12, 31),
                    description="Full stack development using Django and React."
                )
            ],
            education=[
                Education(
                    institution="University of Tech",
                    degree="Bachelor's",
                    field_of_study="Computer Science",
                    start_date=date(2012, 8, 1),
                    end_date=date(2016, 5, 20)
                )
            ],
            skills=[
                Skill(name="Python", level="Expert"),
                Skill(name="Docker", level="Intermediate"),
                Skill(name="AWS", level="Advanced")
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
                    institution=fake.company(), # Close enough for demo
                    degree="Bachelor's",
                    field_of_study="Computer Science",
                    start_date=fake.date_between(start_date='-10y', end_date='-6y'),
                    end_date=fake.date_between(start_date='-6y', end_date='-5y')
                )
            ],
            skills=[Skill(name=fake.word(), level="Intermediate") for _ in range(3)]
        )
        return self.profile
