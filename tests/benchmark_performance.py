import time
import random
from src.modules.job_intelligence import JobScanner
from src.core.models import CandidateProfile, JobOpportunity, Skill, Experience
from faker import Faker

fake = Faker()

def generate_large_profile(num_skills=1000):
    skills = [Skill(name=fake.word(), level="Expert") for _ in range(num_skills)]
    return CandidateProfile(
        name="Test User",
        email="test@example.com",
        phone="123",
        summary="summary",
        skills=skills,
        experiences=[],
        education=[]
    )

def generate_large_job(num_requirements=500):
    requirements = [fake.word() for _ in range(num_requirements)]
    return JobOpportunity(
        id="1",
        title=fake.job(),
        company="Company",
        description="Desc",
        requirements=requirements,
        url="http://example.com",
        source="LinkedIn"
    )

def benchmark():
    scanner = JobScanner()
    profile = generate_large_profile(num_skills=2000)
    job = generate_large_job(num_requirements=1000)

    start_time = time.time()
    iterations = 100
    for _ in range(iterations):
        scanner.calculate_match_score(profile, job)
    end_time = time.time()

    total_time = end_time - start_time
    print(f"Total time for {iterations} iterations: {total_time:.4f} seconds")
    print(f"Average time per iteration: {total_time/iterations:.6f} seconds")

if __name__ == "__main__":
    benchmark()
