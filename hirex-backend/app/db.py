# app/db.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Session, create_engine

from .config import settings

# Import auth models once so they're registered in metadata before create_all()
# (Do NOT import from .db anywhere else to avoid circulars)
from .models_auth import User, AuthTxn  # noqa: F401


class Candidate(SQLModel, table=True):
    __tablename__ = "candidate"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Identity & contacts
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

    # Derived roles (as JSON string list, e.g. ["frontend_software_engineer","devops_engineer"])
    roles: str = "[]"

    # Core numeric/categorical features
    years_experience: Optional[float] = 0.0
    cgpa: Optional[float] = None
    project_count: int = 0
    hackathon_wins: int = 0
    extracurricular_score: int = 0
    leadership_score: int = 0     # general leadership
    por_score: int = 0            # positions of responsibility
    notice_period_months: Optional[float] = None

    # JSON blobs (stored as TEXT)
    skills: str = "[]"
    soft_skills: str = "[]"
    institutions: str = "[]"        # normalized list like ["IIT","NIT","BITS"]
    degrees: str = "[]"             # e.g., ["B.Tech","M.Tech"]
    majors: str = "[]"              # e.g., ["CSE","ECE"]
    languages: str = "[]"
    certifications: str = "[]"
    achievements: str = "[]"
    publications: str = "[]"
    education_entries: str = "[]"   # list[{college, degree, major, start, end, cgpa}]
    experience_entries: str = "[]"  # list[{company, role, start, end, desc, duration_months}]
    projects: str = "[]"            # list[{title, tech, desc, snippet}]
    keywords: str = "[]"
    education_text: Optional[str] = None

    # Raw
    resume_path: str
    parsed_text: str

    created_at: datetime = Field(default_factory=datetime.utcnow)


# Engine
engine = create_engine(settings.DB_URL, echo=False)


def init_db() -> None:
    """Create all tables if they don't exist."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency to yield a SQLModel Session bound to our engine."""
    with Session(engine) as session:
        yield session
