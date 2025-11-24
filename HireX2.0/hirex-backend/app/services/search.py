import json
from typing import List, Optional
from ..db import Candidate

def apply_filters(
    rows: List[Candidate],
    *,
    min_experience: float,
    must_have: List[str],
    education_any_of: List[str],
    location: Optional[str],
    min_projects: int,
    min_cgpa: Optional[float],
    min_hackathon_wins: int,
    contains_phrase: Optional[str],
    require_extracurricular: bool,
    require_por: bool,
    roles_any_of: List[str],  # NEW: role filtering
) -> List[Candidate]:
    must = set(must_have or [])
    edu = set(education_any_of or [])
    roles_req = set(roles_any_of or [])
    phrase = (contains_phrase or "").lower().strip()

    out: List[Candidate] = []
    for r in rows:
        rskills = set(json.loads(r.skills or "[]"))
        rins = set(json.loads(r.institutions or "[]"))
        rprojects = json.loads(r.projects or "[]")
        try:
            rroles = set(json.loads(getattr(r, "roles", "[]") or "[]"))
        except Exception:
            rroles = set()

        # numeric / categorical filters
        if min_experience and (r.years_experience or 0) < min_experience:
            continue
        if must and not must.issubset(rskills):
            continue
        if edu and edu.isdisjoint(rins):
            continue
        if roles_req and roles_req.isdisjoint(rroles):
            continue
        if location and (r.location or "").lower() != (location or "").lower():
            continue
        if min_projects and (r.project_count or 0) < min_projects:
            continue
        if min_cgpa is not None and (r.cgpa or 0) < min_cgpa:
            continue
        if min_hackathon_wins and (r.hackathon_wins or 0) < min_hackathon_wins:
            continue
        if require_extracurricular and (r.extracurricular_score or 0) == 0:
            continue
        if require_por and (r.por_score or 0) == 0:
            continue

        # phrase match in projects or entire text
        if phrase:
            text_low = (r.parsed_text or "").lower()
            in_projects = any(
                phrase in (p.get("title", "").lower() + " " + p.get("desc", "").lower())
                for p in rprojects
            )
            if not (in_projects or (phrase in text_low)):
                continue

        out.append(r)
    return out


def best_snippet(text: str, phrase_or_query: str, window: int = 220) -> str:
    if not text:
        return ""
    q = (phrase_or_query or "").strip()
    if not q:
        return text[:window].replace("\n", " ")
    tl, ql = text.lower(), q.lower()
    i = tl.find(ql)
    if i < 0:
        return text[:window].replace("\n", " ")
    start = max(0, i - window // 2)
    end = min(len(text), start + window)
    return text[start:end].replace("\n", " ")
