from src.core.models import JobOpportunity, CandidateProfile
import random

class InterviewCoach:
    def __init__(self):
        self.common_questions = [
            "Tell me about yourself.",
            "Why do you want to work at {company}?",
            "What is your greatest strength?",
            "Describe a challenging situation you handled."
        ]
        self.tech_questions_pool = [
            "Explain how you would design a scalable system for {topic}.",
            "How do you handle technical debt?",
            "What is your experience with {skill}?",
            "Describe a time you optimized a slow query."
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
            questions.append(f"How have you used {req} in a production environment?")

        # Add a random system design or general tech question
        topic = job.title.split()[-1] if job.title else "software"
        questions.append(random.choice(self.tech_questions_pool).format(topic=topic, skill=random.choice(job.requirements) if job.requirements else "Python"))

        return questions

    def simulate_feedback(self) -> str:
        """
        Simulates feedback after a mock interview.
        """
        feedbacks = [
            "Strong communication skills. Elaborate more on technical details.",
            "Good technical depth. Work on being more concise.",
            "Excellent cultural fit. Ready for the real interview.",
            "Needs more preparation on system design concepts."
        ]
        return random.choice(feedbacks)
