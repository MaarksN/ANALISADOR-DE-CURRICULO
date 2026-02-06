from src.core.models import CandidateProfile, JobOpportunity, Resume
from datetime import datetime

class ResumeGenerator:
    def generate_resume(self, profile: CandidateProfile, job: JobOpportunity) -> Resume:
        """
        Generates a tailored resume for a specific job.
        """
        # Create a header
        content = f"CURRÍCULO: {profile.name}\n"
        content += f"Contato: {profile.email} | {profile.phone}\n"
        content += f"LinkedIn: {profile.linkedin_url}\n\n"

        # Tailored Summary
        content += "RESUMO PROFISSIONAL\n"
        # In a real system, this would rewrite the summary based on job.description
        content += f"{profile.summary}\n"
        content += f"Entusiasta por vagas de {job.title} na {job.company}.\n\n"

        # Skills (Highlighting matching ones)
        content += "HABILIDADES\n"
        skills_list = [s.name for s in profile.skills]
        # Bolding/Highlighting matching skills (simulated with *)
        formatted_skills = []
        # Optimization: Pre-calculate lowercase requirements set for O(1) lookup
        requirements_lower = {r.lower() for r in job.requirements}
        for skill in skills_list:
            if skill.lower() in requirements_lower:
                formatted_skills.append(f"*{skill}*")
            else:
                formatted_skills.append(skill)
        content += ", ".join(formatted_skills) + "\n\n"

        # Experience
        content += "EXPERIÊNCIA\n"
        for exp in profile.experiences:
            content += f"{exp.title} na {exp.company} ({exp.start_date} - {exp.end_date if exp.end_date else 'Atualmente'})\n"
            content += f"- {exp.description}\n"

        content += "\nFORMAÇÃO ACADÊMICA\n"
        for edu in profile.education:
            content += f"{edu.degree} em {edu.field_of_study}, {edu.institution}\n"

        return Resume(
            profile_id=profile.id,
            job_id=job.id,
            content=content,
            version_tag=f"v1-{job.company}-{datetime.now().strftime('%Y%m%d')}"
        )
