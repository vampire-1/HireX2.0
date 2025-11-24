from typing import List, Optional
from pydantic import BaseModel

class UploadResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    skills: List[str]
    institutions: List[str]

class RecruiterQueryRequest(BaseModel):
    prompt: str
    top_k: int = 50
    profile: Optional[str] = None                # "balanced", "cgpa-heavy", etc.
    candidate_ids: Optional[List[int]] = None    # restrict to subset (e.g., "from these resumes")

class StructuredFilters(BaseModel):
    min_experience: float = 0
    must_have_skills: List[str] = []
    education_any_of: List[str] = []
    location: Optional[str] = None
    min_projects: int = 0
    min_cgpa: Optional[float] = None
    min_hackathon_wins: int = 0
    require_extracurricular: bool = False
    require_por: bool = False
    contains_phrase: Optional[str] = None
    roles_any_of: List[str] = []                 # NEW: canonical role tags to match

class CandidateOut(BaseModel):
    id: int
    name: str
    email: Optional[str]
    years_experience: Optional[float]
    skills: List[str]
    institutions: List[str]
    score: float
    reasons: List[str] = []
    resume_path: str
    snippet: Optional[str] = None

class RecruiterSearchResponse(BaseModel):
    query: str
    filters: StructuredFilters
    total_returned: int
    items: List[CandidateOut]
