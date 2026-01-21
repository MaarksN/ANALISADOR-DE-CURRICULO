from src.modules.interview_prep import InterviewCoach
from src.modules.decision_engine import StrategyEngine
from src.core.models import JobOpportunity
from faker import Faker

fake = Faker()

def verify_new_modules():
    print("Testing InterviewCoach...")
    coach = InterviewCoach()
    job = JobOpportunity(
        id="1", title="Senior Python Dev", company="TestCorp",
        description="...", requirements=["Python", "Django"],
        url="...", source="test"
    )
    questions = coach.generate_questions(job)
    assert len(questions) > 0
    print(f"Generated {len(questions)} questions.")
    feedback = coach.simulate_feedback()
    assert isinstance(feedback, str)
    print(f"Feedback: {feedback}")

    print("\nTesting StrategyEngine...")
    engine = StrategyEngine()
    metrics = {"scanned": 100, "matched": 60, "applied": 5, "interviews": 0}
    msg = engine.analyze_performance(metrics, [])
    print(f"Strategy Analysis: {msg}")
    print(f"Current Strategy: {engine.get_current_strategy()}")

    # Test high volume case
    metrics["matched"] = 60
    metrics["applied"] = 2
    engine.analyze_performance(metrics, [])
    assert engine.get_current_strategy() == "High Volume Sprint"

    print("\nAll feature verification tests passed.")

if __name__ == "__main__":
    verify_new_modules()
