from src.core.models import CandidateProfile, JobOpportunity, Resume
from datetime import datetime

class ResumeGenerator:
    def generate_resume(self, profile: CandidateProfile, job: JobOpportunity) -> Resume:
        """
        Generates a tailored resume for a specific job.
        """
        # Create a header
        content = f"RESUME: {profile.name}\n"
        content += f"Contact: {profile.email} | {profile.phone}\n"
        content += f"LinkedIn: {profile.linkedin_url}\n\n"

        # Tailored Summary
        content += "SUMMARY\n"
        # In a real system, this would rewrite the summary based on job.description
        content += f"{profile.summary}\n"
        content += f"Passionate about {job.title} roles at {job.company}.\n\n"

        # Skills (Highlighting matching ones)
        content += "SKILLS\n"
        skills_list = [s.name for s in profile.skills]
        # Bolding/Highlighting matching skills (simulated with *)
        formatted_skills = []
        for skill in skills_list:
            if skill.lower() in [r.lower() for r in job.requirements]:
                formatted_skills.append(f"*{skill}*")
            else:
                formatted_skills.append(skill)
        content += ", ".join(formatted_skills) + "\n\n"

        # Experience
        content += "EXPERIENCE\n"
        for exp in profile.experiences:
            content += f"{exp.title} at {exp.company} ({exp.start_date} - {exp.end_date if exp.end_date else 'Present'})\n"
            content += f"- {exp.description}\n"

        content += "\nEDUCATION\n"
        for edu in profile.education:
            content += f"{edu.degree} in {edu.field_of_study}, {edu.institution}\n"

        return Resume(
            profile_id=profile.id,
            job_id=job.id,
            content=content,
            version_tag=f"v1-{job.company}-{datetime.now().strftime('%Y%m%d')}"
        )
