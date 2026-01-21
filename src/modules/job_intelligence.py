from typing import List
from src.core.models import JobOpportunity
from faker import Faker
import random

fake = Faker()

class JobScanner:
    def __init__(self):
        pass

    def scan_opportunities(self, keywords: List[str]) -> List[JobOpportunity]:
        """
        Simulates scanning job boards (LinkedIn, Indeed, etc.) for opportunities.
        Returns a list of mock JobOpportunity objects.
        """
        opportunities = []
        # Generate some random jobs
        for _ in range(random.randint(5, 10)):
            job_title = fake.job()
            # Ensure some jobs match the keywords for demo purposes
            if random.random() > 0.5 and keywords:
                job_title = f"{random.choice(keywords)} {job_title}"

            requirements = [fake.word() for _ in range(4)]
            # Add matching keywords to requirements occasionally
            if keywords:
                 requirements.extend(random.sample(keywords, k=min(2, len(keywords))))

            job = JobOpportunity(
                id=fake.uuid4(),
                title=job_title,
                company=fake.company(),
                description=fake.catch_phrase(),
                requirements=requirements,
                url=fake.url(),
                source=random.choice(["LinkedIn", "Indeed", "Glassdoor", "Gupy"]),
                match_score=0.0 # To be calculated later
            )
            opportunities.append(job)

        return opportunities

    def calculate_match_score(self, profile, job: JobOpportunity) -> float:
        """
        Calculates a simple match score based on keyword overlap.
        """
        score = 0.0
        # Check title relevance (simplified)
        for skill in profile.skills:
            if skill.name.lower() in job.title.lower():
                score += 30.0
            if skill.name.lower() in [req.lower() for req in job.requirements]:
                score += 10.0

        # Check experience title relevance
        for exp in profile.experiences:
             if exp.title.lower() in job.title.lower():
                 score += 20.0

        # Cap at 100
        return min(100.0, score)
