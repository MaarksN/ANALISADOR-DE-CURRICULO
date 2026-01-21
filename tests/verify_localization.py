from src.modules.onboarding import OnboardingAgent
from src.modules.job_intelligence import JobScanner
from src.modules.resume_generator import ResumeGenerator
from src.modules.interview_prep import InterviewCoach
from src.modules.monitoring import FollowUpAgent
from src.core.models import JobOpportunity, Application, CandidateProfile, Resume
from faker import Faker
import random

fake = Faker('pt_BR')

def verify_localization():
    print("Verificando localização e novos recursos...")

    # 1. Onboarding
    onboarding = OnboardingAgent()
    profile = onboarding.load_default_profile()
    assert "Engenheiro de Software" in profile.summary
    print(f"Perfil carregado (PT-BR): {profile.name} - {profile.summary[:50]}...")

    # 2. Job Scanner
    scanner = JobScanner()
    jobs = scanner.scan_opportunities(["Python"])
    assert len(jobs) > 0
    # Faker job titles might be in PT or English depending on locale implementation in Faker,
    # but let's check if we can run it. Faker pt_BR usually generates PT names/companies.
    print(f"Vaga encontrada: {jobs[0].title} na {jobs[0].company}")

    # 3. Resume
    resume_gen = ResumeGenerator()
    resume = resume_gen.generate_resume(profile, jobs[0])
    assert "RESUMO PROFISSIONAL" in resume.content
    assert "HABILIDADES" in resume.content
    print("Currículo gerado com sucesso em Português.")

    # 4. Interview Prep
    coach = InterviewCoach()
    questions = coach.generate_questions(jobs[0])
    print("Questões de entrevista:")
    for q in questions:
        print(f"- {q}")
    # Simple heuristic check for Portuguese words
    assert "você" in questions[0].lower() or "fale" in questions[0].lower()

    # 5. Monitoring
    monitoring = FollowUpAgent()
    app = Application(
        job_id="123", profile_id=profile.id, resume_id=resume.id,
        status="Aplicado", platform="LinkedIn", notes="Teste"
    )
    # Force follow up check (we need to loop or force probability)
    actions = []
    for _ in range(50): # Try 50 times to hit the 10% chance
        res = monitoring.check_for_follow_up([app])
        if res:
            actions.extend(res)
            break

    if actions:
        print(f"Ação de monitoramento gerada: {actions[0]}")
        assert "Follow-up enviado" in actions[0]
    else:
        print("Nenhum follow-up gerado nesta execução (probabilístico).")

    print("Verificação completa.")

if __name__ == "__main__":
    verify_localization()
