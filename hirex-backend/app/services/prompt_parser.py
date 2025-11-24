import re
from typing import Dict, List
from .skills import extract_skills
from .educations import ELITE_INSTITUTES
from .roles import normalize_role_text, expand_skills_for_roles

def _num_0_10(s: str):
    try:
        v = float(s);  return v if 0.0 <= v <= 10.0 else None
    except Exception:
        return None

def parse_prompt(prompt: str) -> Dict:
    p = prompt.lower()

    # Years
    yrs = 0
    m = re.search(r"(\d+)\s*\+?\s*(?:years|yrs|y)\b", p)
    if m: yrs = int(m.group(1))

    # Roles (normalize)
    roles = normalize_role_text(p)

    # Skills (from text) + expansion from roles
    must = extract_skills(p)
    role_skills = expand_skills_for_roles(roles)
    for s in role_skills:
        if s not in must:
            must.append(s)

    # Education (IIT/NIT/BITS…)
    edu_targets: List[str] = []
    for canon, variants in ELITE_INSTITUTES.items():
        if any(re.search(rf"\b{re.escape(v)}\b", p) for v in variants):
            edu_targets.append(canon)

    # Location (simple)
    loc = None
    m2 = re.search(r"\b(?:in|located in)\s+([a-zA-Z][a-zA-Z\s]+)\b", p)
    if m2: loc = m2.group(1).strip()

    # Projects
    min_projects = 0
    m3 = re.search(r"(?:more than|>=?|at\s*least|minimum|min)\s*(\d+)\s*(?:projects?)", p)
    if m3: min_projects = int(m3.group(1))
    else:
        m3b = re.search(r"(\d+)\s*\+?\s*(?:projects?)", p)
        if m3b: min_projects = max(min_projects, int(m3b.group(1)))

    # CGPA (robust)
    min_cgpa = None
    cgpa_patterns = [
        r"(?:cgpa|gpa)\s*(?:of\s*)?(?:>=|=>|≥|at\s*least|minimum|min|more\s*than|above|over)?\s*([0-9](?:\.[0-9])?)",
        r"(?:>=|=>|≥|at\s*least|minimum|min|more\s*than|above|over)\s*([0-9](?:\.[0-9])?)\s*(?:cgpa|gpa)",
        r"([0-9](?:\.[0-9])?)\s*\+?\s*(?:cgpa|gpa)",
        r"(?:cgpa|gpa)\s*[:=]\s*([0-9](?:\.[0-9])?)",
    ]
    for pat in cgpa_patterns:
        m4 = re.search(pat, p)
        if m4:
            val = _num_0_10(m4.group(1))
            if val is not None:
                min_cgpa = val; break

    # Hackathons
    min_hackathon_wins = 0
    m5 = re.search(r"(?:won|wins?)\s*(?:more than|>=?|at\s*least|minimum|min)?\s*(\d+)\s*(?:hackathons?)", p)
    if m5:
        try: min_hackathon_wins = int(m5.group(1))
        except: pass

    # Phrase
    contains_phrase = None
    m6 = re.search(r"(?:about|with|on|titled|named)\s+\"([^\"]+)\"", p)
    if m6: contains_phrase = m6.group(1)
    else:
        m6b = re.search(r"(?:who|candidate).*?(?:built|made|did)\s+([a-z0-9 \-]+?)\s+(?:project|solution|system)", p)
        if m6b: contains_phrase = m6b.group(1).strip()

    # Extras
    require_extracurricular = any(w in p for w in ["extracurricular", "extra curricular", "club", "fest", "volunteer", "community"])
    require_por = any(w in p for w in ["position of responsibility", "por", "leadership", "president", "secretary", "team lead"])

    return {
        "min_experience": float(yrs),
        "must_have_skills": must,
        "education_any_of": edu_targets,
        "location": loc,
        "min_projects": min_projects,
        "min_cgpa": min_cgpa,
        "min_hackathon_wins": min_hackathon_wins,
        "contains_phrase": contains_phrase,
        "require_extracurricular": require_extracurricular,
        "require_por": require_por,
        "roles_any_of": roles,  # NEW: pass roles through
    }
