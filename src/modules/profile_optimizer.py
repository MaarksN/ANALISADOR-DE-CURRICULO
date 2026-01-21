from src.core.models import CandidateProfile, JobOpportunity

class ProfileOptimizer:
    def optimize_for_job(self, profile: CandidateProfile, job: JobOpportunity) -> CandidateProfile:
        """
        Optimizes the candidate profile for a specific job opportunity.
        In a real scenario, this would use LLM to rewrite the summary and experiences.
        Here, we will simulate it by appending relevant keywords.
        """
        optimized_profile = profile.model_copy(deep=True)

        # Simulated optimization logic
        keywords = job.requirements

        # Append missing keywords to summary to "optimize"
        added_keywords = [k for k in keywords if k.lower() not in optimized_profile.summary.lower()]

        if added_keywords:
            optimized_profile.summary += f"\n\nOptimized focus areas: {', '.join(added_keywords)}."

        return optimized_profile

    def update_linkedin_headline(self, profile: CandidateProfile) -> str:
        """Generates a new LinkedIn headline based on skills."""
        top_skills = [s.name for s in profile.skills[:3]]
        return f"{profile.experiences[0].title} | {' | '.join(top_skills)} | Open to opportunities"
