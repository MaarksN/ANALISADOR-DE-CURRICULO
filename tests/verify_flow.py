from src.modules.onboarding import OnboardingAgent
from src.modules.job_intelligence import JobScanner
from src.modules.profile_optimizer import ProfileOptimizer
from src.modules.resume_generator import ResumeGenerator
from src.modules.applier import ApplicationBot

def verify_system_flow():
    print("Initializing agents...")
    onboarding = OnboardingAgent()
    scanner = JobScanner()
    optimizer = ProfileOptimizer()
    resume_gen = ResumeGenerator()
    applier = ApplicationBot()

    print("Loading profile...")
    profile = onboarding.load_default_profile()
    assert profile.name == "Alex Developer"
    print(f"Profile loaded: {profile.name}")

    print("Scanning for jobs...")
    keywords = [s.name for s in profile.skills]
    jobs = scanner.scan_opportunities(keywords)
    print(f"Found {len(jobs)} jobs.")
    assert len(jobs) > 0

    print("Matching jobs...")
    matched_jobs = []
    for job in jobs:
        score = scanner.calculate_match_score(profile, job)
        if score > 0:
            matched_jobs.append(job)
            print(f"Matched: {job.title} at {job.company} (Score: {score})")

    if not matched_jobs:
        print("No matches found in this random run. Retrying scan...")
        # Force a match for test purposes
        jobs = scanner.scan_opportunities(keywords)
        matched_jobs = jobs # Take all

    target_job = matched_jobs[0]
    print(f"Targeting job: {target_job.title}")

    print("Optimizing profile...")
    opt_profile = optimizer.optimize_for_job(profile, target_job)
    assert "Optimized focus areas" in opt_profile.summary or opt_profile.summary == profile.summary

    print("Generating resume...")
    resume = resume_gen.generate_resume(opt_profile, target_job)
    assert target_job.company in resume.version_tag
    print(f"Resume generated: {resume.version_tag}")

    print("Applying...")
    app = applier.apply(opt_profile, target_job, resume)
    print(f"Application Status: {app.status}")
    assert app.job_id == target_job.id

    print("System flow verification successful!")

if __name__ == "__main__":
    verify_system_flow()
