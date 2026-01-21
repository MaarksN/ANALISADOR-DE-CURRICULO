from src.core.models import Application, JobOpportunity, Resume, CandidateProfile
from datetime import datetime
import random

class ApplicationBot:
    def __init__(self):
        self.application_history = []

    def apply(self, profile: CandidateProfile, job: JobOpportunity, resume: Resume) -> Application:
        """
        Simulates the application process.
        """
        # Simulate network latency or processing time? Not needed for simple logic.

        # Determine success probability (mocking captcha failures or form errors)
        status = "Applied"
        if random.random() < 0.05:
             status = "Failed" # 5% failure rate

        app = Application(
            job_id=job.id,
            profile_id=profile.id,
            resume_id=resume.id,
            status=status,
            platform=job.source,
            notes=f"Applied with resume version {resume.version_tag}"
        )

        self.application_history.append(app)
        return app
