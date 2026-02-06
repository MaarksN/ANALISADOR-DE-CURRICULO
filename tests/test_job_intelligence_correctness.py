import unittest
from datetime import date
from src.modules.job_intelligence import JobScanner
from src.core.models import CandidateProfile, JobOpportunity, Skill, Experience

class TestJobIntelligence(unittest.TestCase):
    def test_calculate_match_score(self):
        scanner = JobScanner()

        # Setup Profile
        skills = [Skill(name="Python", level="Expert"), Skill(name="Docker", level="Intermediate")]
        experiences = [Experience(title="Software Engineer", company="Tech Corp", start_date=date(2020, 1, 1), description="")]
        profile = CandidateProfile(
            name="Test User",
            email="test@example.com",
            phone="123",
            summary="summary",
            skills=skills,
            experiences=experiences,
            education=[]
        )

        # Setup Job
        job = JobOpportunity(
            id="1",
            title="Senior Python Developer",
            company="Company",
            description="Desc",
            requirements=["python", "kubernetes", "docker"],
            url="http://example.com",
            source="LinkedIn"
        )

        # Calculate Score
        # Python in title: +30
        # Python in requirements: +10
        # Docker in requirements: +10
        # Software Engineer not in title: +0
        # Total: 50.0

        score = scanner.calculate_match_score(profile, job)
        self.assertEqual(score, 50.0)

    def test_calculate_match_score_case_insensitive(self):
        scanner = JobScanner()
        skills = [Skill(name="PYTHON", level="Expert")]
        profile = CandidateProfile(
            name="Test User",
            email="test@example.com",
            phone="123",
            summary="summary",
            skills=skills,
            experiences=[],
            education=[]
        )

        job = JobOpportunity(
            id="1",
            title="python developer",
            company="Company",
            description="Desc",
            requirements=["PyThOn"],
            url="http://example.com",
            source="LinkedIn"
        )

        # Python in title: +30
        # Python in requirements: +10
        score = scanner.calculate_match_score(profile, job)
        self.assertEqual(score, 40.0)

if __name__ == '__main__':
    unittest.main()
