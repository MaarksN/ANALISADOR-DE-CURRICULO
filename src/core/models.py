from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import uuid4, UUID

class Experience(BaseModel):
    title: str
    company: str
    start_date: date
    end_date: Optional[date] = None
    description: str

class Education(BaseModel):
    institution: str
    degree: str
    start_date: date
    end_date: Optional[date] = None
    field_of_study: str

class Skill(BaseModel):
    name: str
    level: str  # e.g., Beginner, Intermediate, Expert

class CandidateProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str
    phone: str
    summary: str
    experiences: List[Experience] = []
    education: List[Education] = []
    skills: List[Skill] = []
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None

class JobOpportunity(BaseModel):
    id: str
    title: str
    company: str
    description: str
    requirements: List[str]
    url: str
    source: str # e.g., "LinkedIn", "Indeed"
    match_score: float = 0.0

class Resume(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    job_id: str
    content: str  # The actual text of the resume
    created_at: datetime = Field(default_factory=datetime.now)
    version_tag: str

class Application(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_id: str
    profile_id: UUID
    resume_id: UUID
    status: str = "Applied" # Applied, Interviewing, Rejected, Offer
    applied_at: datetime = Field(default_factory=datetime.now)
    platform: str
    notes: Optional[str] = None
